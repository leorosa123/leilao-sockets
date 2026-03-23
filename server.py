
import socket
import threading
import time
import random
import sys
import queue
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

MAX_CLIENTES = int(sys.argv[1]) if len(sys.argv) > 1 else 3
clientes_ativos = 0

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
# NOVO (Fase 2): Lista de tuplas (conn, nome_usuario, fila_envio) com filas individuais
clientes_conectados = []

# 3. ESTADO GLOBAL DO LEILÃO
indice_item_atual = 0
leilao_geral_ativo = True
item_atual = None
lance_atual = 0.0
vencedor_atual = "nenhum"
tempo_restante = 20
lances_bot = 0
lances_bot_max = 2  

def _thread_envio(conn, fila):
    """Fica em loop retirando mensagens da fila e enviando ao cliente."""
    while True:
        mensagem = fila.get()
        if mensagem is None:
            break
        try:
            conn.sendall(mensagem.encode())
        except Exception:
            break

def enviar_para_todos(mensagem):
    """Envia uma mensagem para todos os clientes usando filas individuais."""
    for conn, _, fila in clientes_conectados:
        try:
            fila.put(mensagem)
        except Exception:
            pass

def gerenciar_leiloes():
    global indice_item_atual, item_atual, lance_atual, vencedor_atual, tempo_restante, leilao_geral_ativo,lances_bot, lances_bot_max

    while indice_item_atual < len(itens_disponiveis) and leilao_geral_ativo:
        with lock:
            item_atual = itens_disponiveis[indice_item_atual]
            lance_atual = item_atual["lance_inicial"]
            vencedor_atual = "nenhum"
            tempo_restante = 20
            lances_bot = 0
            lances_bot_max = random.randint(1, 3)
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
            else:
                for nome, dados in usuarios_db.items():
                    if dados["bloqueado"] > 0:
                        dados["saldo"] += dados["bloqueado"]
                        dados["bloqueado"] = 0.0
                        for c, u, f in clientes_conectados:
                            if u == nome:
                                f.put(
                                    f"[INFO] Saldo desbloqueado. Saldo livre: R$ {dados['saldo']:.2f}\n"
                                )
                nome_exibicao = "Anônimo" if vencedor_atual == "anonimo" else "Ninguém"

            enviar_para_todos(f"\n[ITEM VENDIDO] {item_atual['nome']} arrematado! Vencedor: {nome_exibicao}\n")
        
        # Pausa de 5 segundos antes de puxar o próximo item da lista
        time.sleep(5) 
        indice_item_atual += 1

    enviar_para_todos("\n[INFO] O Leilão acabou! Todos os itens foram vendidos.\n")
    leilao_geral_ativo = False


def simular_usuario():
    global lance_atual, tempo_restante, vencedor_atual, lances_bot, lances_bot_max
    
    while leilao_geral_ativo:
        time.sleep(random.randint(8, 15))
        
        with lock:
            if item_atual is None or tempo_restante <= 0:
                continue
            
            if tempo_restante <= 5:
                continue
            
            if vencedor_atual == "anonimo":
                continue
            
            if lances_bot >= lances_bot_max:
                continue
            
            lance_simulado = lance_atual * random.uniform(1.01, 1.03)
            
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

def processar_cliente(conn, addr):
    global lance_atual, tempo_restante, vencedor_atual, clientes_ativos

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
    # NOVO (Fase 2): Cria fila individual e inicia Thread B de envio para este cliente
    fila_envio = queue.Queue()
    thread_b = threading.Thread(
        target=_thread_envio, args=(conn, fila_envio), daemon=True
    )
    thread_b.start()
    
    with lock:
        if nome_usuario not in usuarios_db:
            usuarios_db[nome_usuario] = {"saldo": 5000.0, "bloqueado": 0.0, "itens": []}
        
        # NOVO (Fase 2): Registra a tupla (conn, nome_usuario, fila_envio) para filas individuais
        clientes_conectados.append((conn, nome_usuario, fila_envio))
        saldo_atual = usuarios_db[nome_usuario]["saldo"]
    
    # NOVO (Fase 2): Handshake de login usa conn.sendall diretamente (antes Thread B estar ativa para mensagens)
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
                    # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                    fila_envio.put(f"[INFO] Tempo restante: {tempo_restante}s\n")

            elif data == ":carteira":
                with lock:
                    usr = usuarios_db[nome_usuario]
                    nomes_dos_itens = [i["nome"] for i in usr["itens"]]
                    lista_txt = ", ".join(nomes_dos_itens) if nomes_dos_itens else "Nenhum"
                    # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                    fila_envio.put(f"[INFO] Saldo Livre: R$ {usr['saldo']:.2f} | Bloqueado: R$ {usr['bloqueado']:.2f}\n")
                    fila_envio.put(f"[INFO] Seus Itens: {lista_txt}\n")
            
            elif data == ":item":
                with lock:
                    if item_atual:
                        # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                        fila_envio.put(f"[INFO] Item na mesa: {item_atual['nome']} | Maior lance: R$ {lance_atual}\n")
            

            elif data.startswith(":vender"):
                nome_item_venda = data.replace(":vender", "").strip()
                if not nome_item_venda:
                    # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                    fila_envio.put("[ALERTA] Uso correto: :vender [Nome do Item]\n")
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
                        
                        # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                        fila_envio.put(f"[INFO] Item '{item_obj['nome']}' vendido! Você pagou R$ {valor_pago:.2f} e recebeu R$ {valor_reembolso:.2f}.\n")
                    else:
                        # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                        fila_envio.put(f"[ALERTA] Você não possui o item: {nome_item_venda}\n")

            else:
                try:
                    valor = float(data)
                    # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                    fila_envio.put(f"[RESPOSTA] Voce executou: LANCE de R$ {valor:.2f}\n")
                    
                    with lock:
                        if not item_atual or tempo_restante <= 0:
                            # NOVO (Fase 2): Usa fila_envio via nova lógica
                            fila_envio.put("[ALERTA] Nenhum leilão rodando. Aguarde o próximo item.\n")
                            continue
                        
                        usr = usuarios_db[nome_usuario]
                        
                        if vencedor_atual == nome_usuario:
                            usr["saldo"] += usr["bloqueado"]
                            usr["bloqueado"] = 0.0
                        
                        if valor <= lance_atual:
                            fila_envio.put(f"[ALERTA] Lance inválido. Mínimo: R$ {lance_atual + 0.01:.2f}\n")
                            continue
                        
                        if usr["saldo"] < valor:
                            fila_envio.put(f"[ALERTA] Saldo insuficiente! Saldo livre: R$ {usr['saldo']:.2f}\n")
                            continue
                    
                        if vencedor_atual in usuarios_db and vencedor_atual != nome_usuario:
                            perdedor = usuarios_db[vencedor_atual]
                            perdedor["saldo"] += perdedor["bloqueado"]
                            perdedor["bloqueado"] = 0.0
                            for c, u, f in clientes_conectados:
                                if u == vencedor_atual:
                                    f.put(f"[ALERTA] Você foi superado! Saldo desbloqueado: R$ {perdedor['saldo']:.2f}\n")
                        
                        usr["saldo"] -= valor
                        usr["bloqueado"] = valor
                        lance_atual = valor
                        tempo_restante = 20
                        vencedor_atual = nome_usuario
                        
                        enviar_para_todos(
                            f"[ITEM]: {item_atual['nome']} | Lance atual: R$ {lance_atual} | Por: {vencedor_atual}\n"
                        )
                        fila_envio.put(f"[INFO] R$ {valor:.2f} bloqueados. Saldo livre: R$ {usr['saldo']:.2f}\n")

                except ValueError:
                    # NOVO (Fase 2): Usa fila_envio em vez de conn.sendall
                    fila_envio.put("[ALERTA] Comando inválido. Digite um número ou :comando\n")

        except Exception:
            break
    
    # Ao sair do loop
    with lock:
        cliente_tuple = (conn, nome_usuario, fila_envio)
        if cliente_tuple in clientes_conectados:
            clientes_conectados.remove(cliente_tuple)
        clientes_ativos -= 1
    
    fila_envio.put(None)
    thread_b.join(timeout=2)
    
    conn.close()
    print(f"{nome_usuario} desconectou.")

# =============================
# INICIALIZAÇÃO DO SERVIDOR
# =============================
if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Servidor iniciado. Limite de conexões simultâneas: {MAX_CLIENTES}")

    # Inicia as threads globais (Leiloeiro + Bot)
    threading.Thread(target=gerenciar_leiloes, daemon=True).start()
    threading.Thread(target=simular_usuario, daemon=True).start()

    # Loop principal para aceitar múltiplos clientes (Fase 2)
    while True:
        try:
            conn, addr = server.accept()
            
            # NOVO (Fase 2): Verifica limite de clientes simultâneos
            with lock:
                lotado = clientes_ativos >= MAX_CLIENTES
            
            if lotado:
                # NOVO (Fase 2): Recusa conexão se o limite máximo foi atingido
                conn.sendall("[ALERTA] Servidor lotado! Tente novamente mais tarde.\n".encode())
                conn.close()
                print(f"Conexão recusada ({addr}): limite de {MAX_CLIENTES} clientes atingido.")
                continue
            
            # NOVO (Fase 2): Registra nova conexão ativa
            with lock:
                clientes_ativos += 1
            
            print(f"Nova conexão de {addr}")
            
            # Cria uma thread para CADA usuário que se conectar
            threading.Thread(target=processar_cliente, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
            leilao_geral_ativo = False
            break


