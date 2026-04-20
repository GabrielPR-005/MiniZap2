import socket
import threading

HOST = '127.0.0.1'
PORT = 5000

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    msg = client.recv(1024).decode('utf-8')
    print("Servidor:", msg)

    username = input("Digite seu username: ")
    client.send(username.encode('utf-8'))

    print("Conectado! Use formato usuario:mensagem\n")

    def receive_messages():
        while True:
            try:
                msg = client.recv(1024).decode('utf-8')
                if msg:
                    print(f"\n{msg}")
                    print("> ", end="", flush=True)
            except:
                break

    threading.Thread(target=receive_messages, daemon=True).start()

    while True:
        try:
            message = input("> ")
            client.send(message.encode('utf-8'))
        except:
            break

if __name__ == "__main__":
    start_client()