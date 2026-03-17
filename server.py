import socket
import threading
import time
import random

HOST = "127.0.0.1"
PORT = 5000

lock = threading.Lock()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Servidor aguardando conexão...")

conn, addr = server.accept()
print("Cliente conectado:", addr)

itens = [
    {"nome": "PlayStation 5", "lance_inicial": 3500},
    {"nome": "Xbox Series X", "lance_inicial": 3200},
    {"nome": "Nintendo Switch", "lance_inicial": 2000},
    {"nome": "RTX 4070", "lance_inicial": 4500}
]

itens_vendidos = []
item_atual = random.choice(itens)
nome_item = item_atual["nome"]
lance_atual = item_atual["lance_inicial"]

tempo_restante = 20
leilao_ativo = True
ultimo_lance_por = "nenhum"
vencedor = "nenhum"

# =============================
# THREAD 1 - PROCESSAR LANCES
# =============================
def processar_lances():
    global lance_atual, tempo_restante, ultimo_lance_por, vencedor, leilao_ativo

    while leilao_ativo:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            if data == ":tempo":
                with lock:
                    tempo = tempo_restante
                conn.sendall(f"[TEMPO RESTANTE]: {tempo}\n".encode())

            elif data == ":item":
                with lock:
                    conn.sendall(f"[ITEM]: {nome_item} | Lance atual: R$ {lance_atual} | Por: {ultimo_lance_por}\n".encode())

            elif data == ":quit":
                conn.sendall("Encerrando conexão...\n".encode())
                leilao_ativo = False
                break

            else:
                try:
                    valor = float(data)
                    with lock:
                        if valor > lance_atual:
                            lance_atual = valor
                            tempo_restante = 20
                            ultimo_lance_por = "cliente"
                            vencedor = "cliente"
                            print(f"Novo lance do cliente: R$ {valor}")
                            
                            # Agora envia QUEM deu o lance
                            conn.sendall(f"[ITEM]: {nome_item} | Lance atual: R$ {lance_atual} | Por: {ultimo_lance_por}\n".encode())
                        else:
                            conn.sendall(f"[LANCE INVÁLIDO]: menor que o atual (R$ {lance_atual})\n".encode())
                except ValueError:
                    # Ignora se não for número (para não travar)
                    pass 
        except Exception:
            break

# =============================
# THREAD 2 - CRONÔMETRO
# =============================
def cronometro():
    global tempo_restante, leilao_ativo

    while leilao_ativo:
        time.sleep(1)
        with lock:
            tempo_restante -= 1
            conn.sendall(f"[TEMPO RESTANTE]: {tempo_restante}\n".encode())

            if tempo_restante <= 0:
                break

    leilao_ativo = False

    with lock:
        resultado = {
            "item": nome_item,
            "valor": lance_atual,
            "vencedor": vencedor
        }
        itens_vendidos.append(resultado)

    # Traduz para aparecer certinho no fim
    vencedor_final = "VOCÊ" if vencedor == "cliente" else ("Anônimo" if vencedor == "anonimo" else "Ninguém")
    
    conn.sendall(f"\n[ITEM VENDIDO] {nome_item} | Valor: R$ {lance_atual:.2f} | Vencedor: {vencedor_final}\n".encode())
    print("\nItem vendido:", resultado)

# =============================
# THREAD 3 - USUÁRIO SIMULADO
# =============================
def simular_usuario():
    global lance_atual, tempo_restante, ultimo_lance_por, vencedor
    i = 0
    
    while i < 4 and leilao_ativo:
        time.sleep(random.randint(5, 10)) # Deixei o bot um pouco mais rápido
        
        with lock:
            if not leilao_ativo or ultimo_lance_por == "anonimo":
                continue

            porcentagem = random.uniform(2, 8)
            lance_simulado = lance_atual * (1 + porcentagem / 100)
            lance_atual = round(lance_simulado, 2)

            tempo_restante = 20
            ultimo_lance_por = "anonimo"
            vencedor = "anonimo"

            print(f"Usuário anônimo fez lance: R$ {lance_atual}")
            # Agora envia QUEM deu o lance
            conn.sendall(f"[ITEM]: {nome_item} | Lance atual: R$ {lance_atual} | Por: {ultimo_lance_por}\n".encode())

        i += 1

# =============================
# INICIAR LEILÃO
# =============================
if __name__ == "__main__":
    # Inicia com quem está vencendo
    conn.sendall(f"[LEILÃO INICIADO] Item: {nome_item} | Lance inicial: R$ {lance_atual} | Por: {ultimo_lance_por}\n".encode())

    thread_receber = threading.Thread(target=processar_lances)
    thread_tempo = threading.Thread(target=cronometro)
    thread_usuario = threading.Thread(target=simular_usuario)

    thread_tempo.start()
    thread_receber.start()
    thread_usuario.start()

    thread_receber.join()
    leilao_ativo = False
    
    print("\nItens vendidos no leilão:")
    for item in itens_vendidos:
        print(item)
    
    conn.close()