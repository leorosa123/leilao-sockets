import socket
import threading
import time
import random

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

print("Cliente conectado:\n", addr)

# Definir as variaveis globais para o leilão
lance_atual = 1000.0 # podemos até aplicar um random depois e adicionair mais valores iniciais 
tempo_restante = 60 # tempo inicial de 1 minuto 
leilao_ativo = True # status do leilão 

lock = threading.Lock() # garantir que duas threads não acessem as variáveis do leilão ao mesmo tempo

# Thread 1 - Processar lances dos clientes
def processar_lances():

    global lance_atual, tempo_restante

    while True:

        try:

            data = conn.recv(1024).decode().strip()

            if not data:
                break

            # Atribuinto primeiro comando de verificar tempo 
            if data == ":tempo":
                #garantir que a leitura do tempo seja feita de forma segura e única 
                with lock:
                    tempo = tempo_restante

                conn.sendall(
                    f"[TEMPO RESTANTE]: {tempo}s\n".encode())
                continue
            elif data == ":item":
                #consultar o lance atual
                with lock:
                    conn.sendall(f"[ITEM ATUAL]: Lance atual é R$ {lance_atual}\n ".encode())
                    continue
            elif data == ":quit":
                #sair do leilão e encerrar a conexão
                with lock:
                    conn.sendall("Encerrando conexão...\n".encode())
                    leilao_ativo = False # garantir que o cronometro pare se a conexão for encerrada
                    break  
            else: 
                # verificar se a entrada é um número (lance) e processar o lance
                try:

                    valor = float(data)
                    # garantir que apenas um lance seja processado por vez
                    with lock:

                        if valor > lance_atual:
                            # resetando o cronometro para 60 segundos a cada novo lance maior
                            lance_atual = valor
                            tempo_restante = 60
                            print(f"Cronometro resetado para 60 segundos devido a novo lance maior: R$ {valor} \n")
                            conn.sendall(
                                f"[NOVO LANCE]: R$ {valor}\n".encode()
                            )

                        else:

                            conn.sendall(
                                f"[LANÇAMENTO INVÁLIDO]: Lance menor que o atual (R$ {lance_atual})\n".encode()
                            )

                except:
                    # se a entrada não for um número, enviar mensagem de erro
                    conn.sendall("Entrada inválida\n".encode())

        except:
            break

# Thread 2 - Cronometro do leilão
def cronometro():

    global tempo_restante, leilao_ativo

    while leilao_ativo:

        time.sleep(1)

        with lock:
            tempo_restante -= 1
            print("Tempo restante:", tempo_restante, "s")

        if tempo_restante <= 0:
            leilao_ativo = False
            # quando tempo acabar, enviar mensagem de encerramento e o valor final do lance
            conn.sendall(f"\n[ITEM VENDIDO] Valor final: R$ {lance_atual}\n".encode())
            break

    print("Tempo encerrado!")


i = 0 
# THREAD 3 - Simulação de usuário anônimo
def simular_usuario():
    global lance_atual, tempo_restante, i

    while i < 4 and leilao_ativo:  # executa apenas 4 vezes

        time.sleep(random.randint(5, 15))  # espera aleatória

        with lock:

            variacao = random.randint(-50, 100)

            lance_simulado = lance_atual + variacao

            # se for maior, aceita como novo lance
            if lance_simulado > lance_atual:

                lance_atual = lance_simulado
                tempo_restante = 60

                conn.sendall(
                    f"[USUÁRIO ANÔNIMO]: novo lance R$ {lance_simulado}\n".encode()
                )
                print(f"Usuário anônimo fez um lance de R$ {lance_simulado} \n")

            else:

                conn.sendall(
                    f"[USUÁRIO ANÔNIMO]: tentou R$ {lance_simulado} (abaixo do atual)\n".encode()
                )
                print(f"Usuário anônimo tentou um lance de R$ {lance_simulado} (abaixo do atual)\n")
        i += 1


thread_receber = threading.Thread(target=processar_lances)

# thread do tempo
thread_tempo = threading.Thread(target=cronometro)

# thread do usuário anônimo
thread_usuario = threading.Thread(target=simular_usuario)

thread_tempo.start()
thread_receber.start()
thread_usuario.start()

# espera as threads terminarem
thread_receber.join()
leilao_ativo = False # esperar o client finalziar a conexão para encerrar o leilão
thread_usuario.join()
thread_tempo.join()

conn.close()