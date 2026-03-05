import socket

# endereço IP e porta do servidor
HOST = "127.0.0.1"
PORT = 5000

#criando o socket do servidor
# conexão TCP/IP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
# servidor começa a ouvir pelas conexões 
server.listen(1)

print("Servidor aguardando conexão...")

# addr é o endereço do cliente e conn o socket de conexão com o cliente
conn, addr = server.accept()

print("Cliente conectado:", addr)

while True:
    # recebendo os dados do cliente em até 1024 bytes  
    data = conn.recv(1024).decode()

    if not data:
        break

    print("Cliente enviou:", data)

conn.close()