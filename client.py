import socket
import threading
from time import sleep

# endereço IP e porta do servidor
HOST = "127.0.0.1"
PORT = 5000

# lock para controlar escrita no terminal
print_lock = threading.Lock()

# função para enviar mensagens ao servidor
def enviar(sock):

    while True:
        
        msg = input("Digite comando ou lance: ")

        sock.send(msg.encode())

        if msg == ":quit":
            break
        
#função para receber mensagens do servidor
def receber(sock):

    while True:
        buffer = ""

        try:

            msg = sock.recv(1024).decode()

            if not msg:
                break

            buffer += msg

            while "\n" in buffer:

                mensagem, buffer = buffer.split("\n", 1)
                print("\nServidor:", mensagem)
            
        except:
            break

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

# criando threads para enviar e receber mensagens simultaneamente
t1 = threading.Thread(target=enviar, args=(client,))
t2 = threading.Thread(target=receber, args=(client,))

t1.start()
t2.start()

t1.join()
t2.join()
