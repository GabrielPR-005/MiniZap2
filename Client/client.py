import socket

HOST = '127.0.0.1'  
PORT = 5000         

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Recebe pedido de autenticação
    msg = client.recv(1024).decode('utf-8')
    print("Servidor:", msg)

    # Envia username
    username = input("Digite seu username: ")
    client.send(username.encode('utf-8'))

    print("Conectado! Digite mensagens:\n")

    # Loop de envio
    while True:
        message = input()
        client.send(message.encode('utf-8'))
import socket

HOST = '127.0.0.1'
PORT = 5000

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Recebe pedido de autenticação
    msg = client.recv(1024).decode('utf-8')
    print("Servidor:", msg)

    # Envia username
    username = input("Digite seu username: ")
    client.send(username.encode('utf-8'))

    print("Conectado! Digite mensagens:\n")

    # Thread pra receber mensagens
    def receive_messages():
        while True:
            try:
                msg = client.recv(1024).decode('utf-8')
                print(msg)
            except:
                break

    import threading
    threading.Thread(target=receive_messages, daemon=True).start()

    # Loop de envio
    while True:
        message = input()
        client.send(message.encode('utf-8'))

if __name__ == "__main__":
    start_client()
if __name__ == "__main__":
    start_client()