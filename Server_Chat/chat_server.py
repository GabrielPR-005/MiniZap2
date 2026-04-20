import socket
import threading

HOST = '127.0.0.1'
PORT = 5000

clients = {}

# 🔌 conexão com DB Server
def save_message_to_db(sender, target, message):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('127.0.0.1', 6000))

        payload = f"SAVE|{sender}|{target}|{message}"
        db_socket.send(payload.encode('utf-8'))

        db_socket.close()
    except:
        print("[ERRO] DB Server offline")


def get_old_messages(username, client_socket):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('127.0.0.1', 6000))

        payload = f"GET|{username}"
        db_socket.send(payload.encode('utf-8'))

        data = db_socket.recv(4096).decode('utf-8')
        if data:
            client_socket.send(f"\n=== HISTÓRICO ===\n{data}".encode('utf-8'))

        db_socket.close()
    except:
        print("[ERRO] Não conseguiu buscar histórico")


def handle_client(client_socket, address):
    username = None
    try:
        client_socket.send("USER_AUTH".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8')

        if username in clients:
            client_socket.send("ERRO: Usuário já online.".encode('utf-8'))
            client_socket.close()
            return

        clients[username] = client_socket
        print(f"[CONEXÃO] {username} conectado via {address}")

        # 🔥 Busca histórico
        get_old_messages(username, client_socket)

        broadcast(f"{username} entrou no chat!", "SISTEMA")

        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            if ":" in message:
                target, msg_content = message.split(":", 1)
                send_private_message(username, target, msg_content)
            else:
                broadcast(message, username)

    except Exception as e:
        print(f"[ERRO] {username}: {e}")
    finally:
        if username in clients:
            del clients[username]
            broadcast(f"{username} saiu do chat.", "SISTEMA")
        client_socket.close()


def send_private_message(sender, target, message):
    # 💾 salva no banco
    save_message_to_db(sender, target, message)

    if target in clients:
        payload = f"[Privado de {sender}]: {message}"
        clients[target].send(payload.encode('utf-8'))
    else:
        clients[sender].send(f"USUÁRIO {target} OFFLINE.".encode('utf-8'))


def broadcast(message, sender):
    payload = f"[{sender}]: {message}"
    for user, sock in clients.items():
        if user != sender:
            try:
                sock.send(payload.encode('utf-8'))
            except:
                continue


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