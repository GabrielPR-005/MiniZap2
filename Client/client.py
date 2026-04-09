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

if __name__ == "__main__":
    start_client()