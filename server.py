import socket
import threading
import time

# endereço IP e porta do servidor
HOST = "127.0.0.1"
PORT = 5000

tempo_restante = 60
lock = threading.Lock()

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


def receber_mensagens():

    while True:

        try:
            # mensagem recebida do cliente, decodificada para string
            data = conn.recv(1024).decode()

            if not data:
                break

            print("Cliente enviou:", data)

            conn.send(f"Servidor recebeu: {data}".encode())

        except:
            break


# THREAD DO TEMPO
def cronometro():

    global tempo_restante

    while tempo_restante > 0:

        time.sleep(1)

        with lock:
            tempo_restante -= 1
            print("Tempo restante:", tempo_restante)

    print("Tempo encerrado!")


thread_receber = threading.Thread(target=receber_mensagens)

# thread do tempo
thread_tempo = threading.Thread(target=cronometro)

thread_receber.start()
thread_tempo.start()

# espera as threads terminarem
thread_receber.join()
thread_tempo.join()

conn.close()