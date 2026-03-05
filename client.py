import socket

# endereço IP e porta do servidor
HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# se conecta ao servidor
client.connect((HOST, PORT))

while True:
    # enivar uma menssagem teste ao server 
    msg = input("Digite algo: ")
    # envia a menssagem codificada para o servidor
    client.send(msg.encode())

    if msg == "sair":
        break

client.close()