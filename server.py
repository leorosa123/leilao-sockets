import socket
import threading
import time
import random
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

lock = threading.Lock()

# 1. LISTA DE ITENS (Todos abaixo de 5.000)
itens_disponiveis = [
    {"nome": "Nintendo Switch", "lance_inicial": 1500},
    {"nome": "PlayStation 5", "lance_inicial": 3500},
    {"nome": "Xbox Series X", "lance_inicial": 3200},
    {"nome": "Cadeira Gamer", "lance_inicial": 800},
    {"nome": "Monitor Ultrawide", "lance_inicial": 2100}
]

# 2. BANCO DE DADOS DOS USUÁRIOS E CONEXÕES
# Formato: {"nome_do_usuario": {"saldo": 5000.0, "bloqueado": 0.0, "itens": []}}
usuarios_db = {} 
clientes_conectados = [] # Lista de tuplas (conn, nome_usuario) para enviar mensagens a todos

# 3. ESTADO GLOBAL DO LEILÃO
indice_item_atual = 0
leilao_geral_ativo = True
item_atual = None
lance_atual = 0.0
vencedor_atual = "nenhum"
tempo_restante = 20
lances_bot = 0  

def enviar_para_todos(mensagem):
    """Envia uma mensagem para todos os clientes conectados simultaneamente."""
    for conn, _ in clientes_conectados:
        try:
            conn.sendall(mensagem.encode())
        except Exception:
            pass

# =============================
# THREAD DO LEILOEIRO (LOOP DE ITENS)
# =============================
def gerenciar_leiloes():
    global indice_item_atual, item_atual, lance_atual, vencedor_atual, tempo_restante, leilao_geral_ativo,lances_bot 

    while indice_item_atual < len(itens_disponiveis) and leilao_geral_ativo:
        with lock:
            item_atual = itens_disponiveis[indice_item_atual]
            lance_atual = item_atual["lance_inicial"]
            vencedor_atual = "nenhum"
            tempo_restante = 20
            lances_bot = 0
        enviar_para_todos(f"\n[LEILÃO INICIADO] Item: {item_atual['nome']} | Lance inicial: R$ {lance_atual} | Por: {vencedor_atual}\n")
        enviar_para_todos(f"[ITEM]: {item_atual['nome']} | Lance atual: R$ {lance_atual} | Por: {vencedor_atual}\n")
        
        # Cronômetro do item atual
        while tempo_restante > 0 and leilao_geral_ativo:
            time.sleep(1)
            with lock:
                tempo_restante -= 1
                enviar_para_todos(f"[TEMPO RESTANTE]: {tempo_restante}\n")

        # Fim do tempo do item atual: Entregar item ao vencedor
        with lock:
            if vencedor_atual in usuarios_db:
                usuarios_db[vencedor_atual]["bloqueado"] = 0.0
                item_com_preco = {"nome": item_atual["nome"], "pago": lance_atual}
                usuarios_db[vencedor_atual]["itens"].append(item_com_preco)
                nome_exibicao = vencedor_atual
            elif vencedor_atual == "anonimo":
                nome_exibicao = "Anônimo"
            else:
                nome_exibicao = "Ninguém"

            enviar_para_todos(f"\n[ITEM VENDIDO] {item_atual['nome']} arrematado! Vencedor: {nome_exibicao}\n")
        
        # Pausa de 5 segundos antes de puxar o próximo item da lista
        time.sleep(5) 
        indice_item_atual += 1

    enviar_para_todos("\n[INFO] O Leilão acabou! Todos os itens foram vendidos.\n")
    leilao_geral_ativo = False

# =============================
# THREAD DO BOT
# =============================
def simular_usuario():
    global lance_atual, tempo_restante, vencedor_atual, lances_bot
    
    while leilao_geral_ativo:
        time.sleep(random.randint(6, 12))
        
        with lock:
            if item_atual is None or tempo_restante <= 0:
                continue
            
            if vencedor_atual == "anonimo":
                continue
            
            if lances_bot >= 3:
                continue
            
            lance_simulado = lance_atual * random.uniform(1.02, 1.08)
            
            # Reembolsa o vencedor anterior
            if vencedor_atual in usuarios_db:
                usr = usuarios_db[vencedor_atual]
                usr["saldo"] += usr["bloqueado"]
                usr["bloqueado"] = 0.0
            
            lance_atual = round(lance_simulado, 2)
            tempo_restante = 20
            vencedor_atual = "anonimo"
            
            lances_bot += 1  

            enviar_para_todos(
                f"[ITEM]: {item_atual['nome']} | Lance atual: R$ {lance_atual} | Por: {vencedor_atual}\n"
            )

# =============================
# THREAD DE CADA CLIENTE CONECTADO
# =============================
def processar_cliente(conn, addr):
    global lance_atual, tempo_restante, vencedor_atual

    # 1. IDENTIFICAÇÃO DO USUÁRIO
    conn.sendall("Por favor, digite seu NOME DE USUÁRIO: ".encode())
    try:
        nome_usuario = conn.recv(1024).decode().strip()
        if not nome_usuario:
            conn.close()
            return
    except:
        conn.close()
        return

    # 2. SISTEMA DE SALDO (Cria conta com 5000 ou recupera existente)
    with lock:
        if nome_usuario not in usuarios_db:
            usuarios_db[nome_usuario] = {"saldo": 5000.0, "bloqueado": 0.0, "itens": []}
        
        clientes_conectados.append((conn, nome_usuario))
        saldo_atual = usuarios_db[nome_usuario]["saldo"]
    
    horario = datetime.now().strftime("%H:%M:%S")
    conn.sendall(f"{horario}: CONECTADO!!\n".encode())
    conn.sendall(f"[INFO] Bem-vindo {nome_usuario}! Você tem R$ {saldo_atual:.2f} de crédito livre.\n".encode())
    
    with lock:
        if item_atual:
            conn.sendall(f"[ITEM]: {item_atual['nome']} | Lance atual: R$ {lance_atual} | Por: {vencedor_atual}\n".encode())

    # 4. LOOP DE COMANDOS DO CLIENTE
    while leilao_geral_ativo:
        try:
            data = conn.recv(1024).decode().strip()
            if not data: break

            if data == ":quit":
                break
                
            elif data == ":tempo":
                with lock:
                    conn.sendall(f"[INFO] Tempo restante: {tempo_restante}s\n".encode())

            elif data == ":carteira":
                with lock:
                    usr = usuarios_db[nome_usuario]
                    nomes_dos_itens = [i["nome"] for i in usr["itens"]]
                    lista_txt = ", ".join(nomes_dos_itens) if nomes_dos_itens else "Nenhum"
                    conn.sendall(f"[INFO] Saldo Livre: R$ {usr['saldo']:.2f} | Bloqueado: R$ {usr['bloqueado']:.2f}\n".encode())
                    conn.sendall(f"[INFO] Seus Itens: {lista_txt}\n".encode())
            
            elif data == ":item":
                with lock:
                    if item_atual:
                        conn.sendall(f"[INFO] Item na mesa: {item_atual['nome']} | Maior lance: R$ {lance_atual}\n".encode())
            

            elif data.startswith(":vender"):
                nome_item_venda = data.replace(":vender", "").strip()
                if not nome_item_venda:
                    conn.sendall("[ALERTA] Uso correto: :vender [Nome do Item]\n".encode())
                    continue

                with lock:
                    usr = usuarios_db[nome_usuario]
                    # Busca o item dentro da lista de dicionários
                    item_obj = next((i for i in usr["itens"] if i["nome"].lower() == nome_item_venda.lower()), None)

                    if item_obj:
                        valor_pago = item_obj["pago"]
                        valor_reembolso = valor_pago * 0.9  # 90% do valor real pago
                        
                        usr["itens"].remove(item_obj)
                        usr["saldo"] += valor_reembolso
                        
                        conn.sendall(f"[INFO] Item '{item_obj['nome']}' vendido! Você pagou R$ {valor_pago:.2f} e recebeu R$ {valor_reembolso:.2f}.\n".encode())
                    else:
                        conn.sendall(f"[ALERTA] Você não possui o item: {nome_item_venda}\n".encode())

            else:
                try:
                    valor = float(data)
                    conn.sendall(f"[RESPOSTA] Voce executou: LANCE de R$ {valor:.2f}\n".encode())
                    
                    with lock:
                        if not item_atual or tempo_restante <= 0:
                            conn.sendall(f"[ALERTA] Nenhum leilão rodando no momento. Aguarde o próximo item.\n".encode())
                            continue
                        
                        if valor > lance_atual:
                            usr = usuarios_db[nome_usuario]

                            saldo_total = usr["saldo"] + usr["bloqueado"]

                            if saldo_total >= valor:

                                #  Se outra pessoa estava ganhando → devolve
                                if vencedor_atual in usuarios_db and vencedor_atual != nome_usuario:
                                    usuarios_db[vencedor_atual]["saldo"] += usuarios_db[vencedor_atual]["bloqueado"]
                                    usuarios_db[vencedor_atual]["bloqueado"] = 0.0
                                
                                #  Se o próprio usuário está aumentando o lance
                                if vencedor_atual == nome_usuario:
                                    usr["saldo"] += usr["bloqueado"]
                                    usr["bloqueado"] = 0.0

                                #  Bloqueia o novo valor
                                usr["saldo"] -= valor
                                usr["bloqueado"] = valor
                                
                                lance_atual = valor
                                tempo_restante = 20
                                vencedor_atual = nome_usuario
                                
                                enviar_para_todos(
                                    f"[ITEM]: {item_atual['nome']} | Lance atual: R$ {lance_atual} | Por: {vencedor_atual}\n"
                                )

                                conn.sendall(
                                    f"[INFO] R$ {valor:.2f} bloqueados. Saldo livre: R$ {usr['saldo']:.2f}\n".encode()
                                )

                            else:
                                conn.sendall(
                                    f"[ALERTA] Saldo insuficiente! Total disponível: R$ {saldo_total:.2f}\n".encode()
                                )

                        else:
                            conn.sendall(
                                f"[ALERTA] Lance inválido. Min: R$ {lance_atual + 0.01:.2f}\n".encode()
                            )

                except ValueError:
                    conn.sendall(f"[ALERTA] Comando inválido. Digite um número ou :comando\n".encode())

        except Exception:
            break
    
    # Ao sair do loop
    with lock:
        if (conn, nome_usuario) in clientes_conectados:
            clientes_conectados.remove((conn, nome_usuario))
    conn.close()
    print(f"{nome_usuario} desconectou.")

# =============================
# INICIALIZAÇÃO DO SERVIDOR
# =============================
if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print("Servidor aguardando conexões...")

    # Inicia as threads globais
    threading.Thread(target=gerenciar_leiloes, daemon=True).start()
    threading.Thread(target=simular_usuario, daemon=True).start()

    # Loop principal para aceitar múltiplos clientes (Fase 2)
    while True:
        try:
            conn, addr = server.accept()
            print(f"Nova conexão de {addr}")
            
            # Cria uma thread para CADA usuário que se conectar
            threading.Thread(target=processar_cliente, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
            leilao_geral_ativo = False
            break


