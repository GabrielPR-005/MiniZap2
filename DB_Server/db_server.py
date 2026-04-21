import socket
import threading
import psycopg2

HOST = '127.0.0.1'
PORT = 6000

conn = psycopg2.connect(
    dbname="minizap2",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()
lock = threading.Lock()


def save_message(sender, receiver, message):
    with lock:
        cursor.execute(
            "INSERT INTO messages (sender, receiver, message, status) VALUES (%s, %s, %s, %s)",
            (sender, receiver, message, "enviado")
        )
        conn.commit()


def get_messages(username):
    with lock:
        cursor.execute(
            "SELECT sender, message, timestamp, status FROM messages WHERE receiver = %s ORDER BY timestamp ASC",
            (username,)
        )
        messages = cursor.fetchall()

        cursor.execute(
            "UPDATE messages SET status = 'entregue' WHERE receiver = %s AND status = 'enviado'",
            (username,)
        )
        conn.commit()

        return messages


def handle_db_client(client_socket, address):
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            parts = data.split("|")

            if parts[0] == "SAVE":
                _, sender, receiver, message = parts
                save_message(sender, receiver, message)
                client_socket.send("OK".encode('utf-8'))

            elif parts[0] == "GET":
                _, username = parts
                messages = get_messages(username)

                response = ""
                for sender, msg, ts, status in messages:
                    response += f"[{ts}] {sender}: {msg} ({status})\n"

                if response == "":
                    response = "Nenhuma mensagem encontrada.\n"

                client_socket.send((response + "<END>").encode('utf-8'))

            elif parts[0] == "UPDATE":
                _, msg_id, status = parts

                cursor.execute(
                    "UPDATE messages SET status = %s WHERE id = %s",
                    (status, msg_id)
                )
                conn.commit()

                client_socket.send("OK".encode('utf-8'))

            else:
                client_socket.send("INVALID_COMMAND<END>".encode('utf-8'))

    except Exception as e:
        print(f"[ERRO DB] {address}: {e}")
    finally:
        client_socket.close()


def start_db_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[DB SERVER] Rodando em {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_db_client, args=(client_sock, addr))
        thread.start()


if __name__ == "__main__":
    start_db_server()