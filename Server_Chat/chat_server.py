import socket
import threading

# Configurações de rede
HOST = '127.0.0.1'  # IP do Server de Chat
PORT = 5000         # Porta para conexões de client

# Lista de clientes conectados: {username: socket_obj}
clients = {}

def handle_client(client_socket, address):
    
    # Lida com a comunicação individual de cada cliente.
    
    username = None
    try:
        #Fase de Identificação (Login Simples)
        client_socket.send("USER_AUTH".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8')
        
        if username in clients:
            client_socket.send("ERRO: Usuário já online.".encode('utf-8'))
            client_socket.close()
            return

        clients[username] = client_socket
        print(f"[CONEXÃO] {username} conectado via {address}")
        broadcast(f"{username} entrou no chat!", "SISTEMA")

        #Loop de Mensagens
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            
            # Lógica de Entrega (Exemplo: "destino:mensagem")
            if ":" in message:
                target, msg_content = message.split(":", 1)
                send_private_message(username, target, msg_content)
            else:
                broadcast(message, username)

    except Exception as e:
        print(f"[ERRO] Erro com {username}: {e}")
    finally:

        #Desconexão
        if username in clients:
            del clients[username]
            broadcast(f"{username} saiu do chat.", "SISTEMA")
        client_socket.close()

def send_private_message(sender, target, message):
    
    #Envia mensagem para um usuário específico e simula persistência.
    
    #TO DO, FAZER AINDA: FAZER chamada de rede para o BD_Server.py
    
    if target in clients:
        payload = f"[Privado de {sender}]: {message}"
        clients[target].send(payload.encode('utf-8'))
    else:
        clients[sender].send(f"USUÁRIO {target} OFFLINE.".encode('utf-8'))

def broadcast(message, sender):
    #Envia mensagem para todos os conectados.
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
    print(f"[LISTENING] Servidor de Chat rodando em {HOST}:{PORT}")

    while True:
        client_sock, addr = server.accept()
        # Cria uma thread para cada novo cliente
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()

if __name__ == "__main__":
    start_server()