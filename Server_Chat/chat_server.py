import socket
import threading

# Configuração do servidor
HOST = '26.15.73.85'
PORT = 5000

# Dicionário que armazena usuários conectados: {username: socket}
clients = {}

# Lock para evitar problemas de concorrência ao acessar "clients"
clients_lock = threading.Lock()


# =========================
# FUNÇÃO: salvar mensagem no banco
# =========================
def save_message_to_db(sender, target, message):
    try:
        # Cria conexão com servidor de banco
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('26.15.73.85', 6000))
        #Cria socket TCP (comunicação confiável)
        #Conecta no servidor de banco 

        # Envia comando para salvar mensagem
        payload = f"SAVE|{sender}|{target}|{message}"
        db_socket.send(payload.encode('utf-8'))
        #Monta comando formadto: ACAO/rementente/destinario/mensagem e envia em bytes


        # Recebe resposta do DB
        response = db_socket.recv(1024).decode('utf-8')

        db_socket.close()
        #fecha conexao

    except Exception as e:
        print("[ERRO] DB Server offline", e)


# =========================
# FUNÇÃO: atualizar status da mensagem
# =========================
def update_status(msg_id, status):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('26.15.73.85', 6000))

        payload = f"UPDATE|{msg_id}|{status}"
        db_socket.send(payload.encode('utf-8'))
        # atualiza a mensagem

        db_socket.recv(1024)
        db_socket.close()
    except:
        pass


# =========================
# FUNÇÃO: buscar histórico de mensagens
# =========================
def get_old_messages(username, client_socket):
    try:
        db_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        db_socket.connect(('26.15.73.85', 6000))

        # Solicita mensagens do usuário
        payload = f"GET|{username}"
        db_socket.send(payload.encode('utf-8'))

        data = ""
        while True:
            part = db_socket.recv(1024).decode('utf-8')
            data += part
            if "<END>" in part:
                break
        # Loop para receber dados em partes (caso seja grande)

        data = data.replace("<END>", "")

        # Envia histórico para o cliente
        if data:
            client_socket.send(f"\n= HISTÓRICO =\n{data}".encode('utf-8'))

        db_socket.close()
    except Exception as e:
        print("[ERRO] Histórico", e)


# =========================
# FUNÇÃO: envio de mensagem privada
# =========================
def send_private_message(sender, target, message):
    # Salva mensagem no banco / garante persistência
    save_message_to_db(sender, target, message)

    # Verifica se destinatário está online
    with clients_lock:
        if target in clients:
            payload = f"[Privado de {sender}]: {message}"

            try:
                # Envia mensagem
                clients[target].send(payload.encode('utf-8'))

                # Log de status
                print(f"[STATUS] {sender}->{target}: ENTREGUE")

            except:
                # Remove cliente se desconectado
                del clients[target]
        else:
            # Caso esteja offline
            clients[sender].send(
                f"Mensagem enviada para {target} (aguardando entrega)".encode('utf-8')
            )


# =========================
# FUNÇÃO: broadcast (mensagem para todos)
# =========================
def broadcast(message, sender):
    payload = f"[{sender}]: {message}"

    with clients_lock:
        for user, sock in clients.items(): # percorre todos conectados
            if user != sender:              # não manda pra si mesmo
                try:
                    sock.send(payload.encode('utf-8'))
                except:
                    continue


# =========================
# FUNÇÃO PRINCIPAL DE CADA CLIENTE
# =========================
def handle_client(client_socket, address):
    username = None
    try:
        # Solicita username
        client_socket.send("USER_AUTH".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8')

        # Controle de concorrência ao adicionar usuário
        with clients_lock:
            if username in clients:
                client_socket.send("ERRO: Usuário já online.".encode('utf-8'))
                client_socket.close()
                return

            clients[username] = client_socket

        print(f"[CONEXÃO] {username} conectado via {address}")

        # Envia histórico
        get_old_messages(username, client_socket)

        # Notifica outros usuários
        broadcast(f"{username} entrou no chat!", "SISTEMA")

        # Loop principal de mensagens
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            # Confirmação de leitura
            if message.startswith("READ:"):
                print(f"[STATUS] mensagem lida por {username}")
                continue

            # Mensagem privada (formato: usuario:mensagem)
            if ":" in message:
                target, msg_content = message.split(":", 1)
                print(f"[MSG] {username} -> {target}: {msg_content}")
                send_private_message(username, target, msg_content)
            else:
                # Broadcast
                broadcast(message, username)

    except Exception as e:
        print(f"[ERRO] {username}: {e}")

    finally:
        # Remove usuário ao desconectar
        with clients_lock:
            if username in clients:
                del clients[username]

        broadcast(f"{username} saiu do chat.", "SISTEMA")
        client_socket.close()


# =========================
# INICIALIZAÇÃO DO SERVIDOR
# =========================
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[CHAT SERVER] Rodando em {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()

        # Cada cliente roda em uma thread (concorrência)
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()


if __name__ == "__main__":
    start_server()