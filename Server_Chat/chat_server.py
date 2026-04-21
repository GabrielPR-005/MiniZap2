import socket
import threading

HOST = '127.0.0.1'
PORT = 5000

clients = {}
clients_lock = threading.Lock()


def save_message_to_db(sender, target, message):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('127.0.0.1', 6000))

        payload = f"SAVE|{sender}|{target}|{message}"
        db_socket.send(payload.encode('utf-8'))

        response = db_socket.recv(1024).decode('utf-8')
        db_socket.close()

    except Exception as e:
        print("[ERRO] DB Server offline", e)


def update_status(msg_id, status):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('127.0.0.1', 6000))

        payload = f"UPDATE|{msg_id}|{status}"
        db_socket.send(payload.encode('utf-8'))

        db_socket.recv(1024)
        db_socket.close()
    except:
        pass


def get_old_messages(username, client_socket):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('127.0.0.1', 6000))

        payload = f"GET|{username}"
        db_socket.send(payload.encode('utf-8'))

        data = ""
        while True:
            part = db_socket.recv(1024).decode('utf-8')
            data += part
            if "<END>" in part:
                break

        data = data.replace("<END>", "")

        if data:
            client_socket.send(f"\n= HISTÓRICO =\n{data}".encode('utf-8'))

        db_socket.close()
    except Exception as e:
        print("[ERRO] Histórico", e)


def send_private_message(sender, target, message):
    save_message_to_db(sender, target, message)

    with clients_lock:
        if target in clients:
            payload = f"[Privado de {sender}]: {message}"

            try:
                clients[target].send(payload.encode('utf-8'))
                print(f"[STATUS] {sender}->{target}: ENTREGUE")

            except:
                del clients[target]
        else:
            clients[sender].send(
                f"Mensagem enviada para {target} (aguardando entrega)".encode('utf-8')
            )


def broadcast(message, sender):
    payload = f"[{sender}]: {message}"
    with clients_lock:
        for user, sock in clients.items():
            if user != sender:
                try:
                    sock.send(payload.encode('utf-8'))
                except:
                    continue


def handle_client(client_socket, address):
    username = None
    try:
        client_socket.send("USER_AUTH".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8')

        with clients_lock:
            if username in clients:
                client_socket.send("ERRO: Usuário já online.".encode('utf-8'))
                client_socket.close()
                return

            clients[username] = client_socket

        print(f"[CONEXÃO] {username} conectado via {address}")

        get_old_messages(username, client_socket)
        broadcast(f"{username} entrou no chat!", "SISTEMA")

        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            if message.startswith("READ:"):
                print(f"[STATUS] mensagem lida por {username}")
                continue

            if ":" in message:
                target, msg_content = message.split(":", 1)
                print(f"[MSG] {username} -> {target}: {msg_content}")
                send_private_message(username, target, msg_content)
            else:
                broadcast(message, username)

    except Exception as e:
        print(f"[ERRO] {username}: {e}")

    finally:
        with clients_lock:
            if username in clients:
                del clients[username]

        broadcast(f"{username} saiu do chat.", "SISTEMA")
        client_socket.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[CHAT SERVER] Rodando em {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()


if __name__ == "__main__":
    start_server()