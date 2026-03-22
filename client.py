import socket
import threading
import os
import sys

HOST = "127.0.0.1"
PORT = 5000

item = "Aguardando..."
lance = "0.00"
tempo = "20"
vencedor = "Ninguém"
running = True

notificacoes = [] 
lock = threading.Lock()

if os.name == 'nt':
    os.system("")

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def adicionar_notificacao(msg):
    global notificacoes
    with lock:
        notificacoes.append(msg)
        if len(notificacoes) > 5: 
            notificacoes.pop(0)

def desenhar():
    with lock:
        sys.stdout.write("\0337\033[H")
        
        # Aumentamos todos os 60 para 80 para dar espaço para as mensagens longas
        sys.stdout.write("=" * 80 + "\n")
        sys.stdout.write("               PAINEL DE LEILÃO".ljust(80) + "\n")
        sys.stdout.write("=" * 80 + "\n")
        sys.stdout.write(f"Item: {item}".ljust(80) + "\n")
        sys.stdout.write(f"Lance atual: R$ {lance}".ljust(80) + "\n")
        sys.stdout.write(f"Vencendo agora: {vencedor}".ljust(80) + "\n")
        sys.stdout.write(f"Tempo restante: {tempo}s".ljust(80) + "\n")
        sys.stdout.write("=" * 80 + "\n")
        
        sys.stdout.write(" COMANDOS DISPONÍVEIS".ljust(80) + "\n")
        sys.stdout.write(" [VALOR] Dar lance  | [:carteira] Ver saldo e itens".ljust(80) + "\n")
        sys.stdout.write(" [:vender NOME] Vender item (90% retorno) | [:quit] Sair".ljust(80) + "\n") # Nova linha
        sys.stdout.write("=" * 80 + "\n")
        
        sys.stdout.write(" NOTIFICAÇÕES & ALERTAS".ljust(80) + "\n")
        sys.stdout.write("-" * 80 + "\n")
        
        linhas_vazias = 5 - len(notificacoes)
        for notif in notificacoes:
            # Aumentamos o limite de corte de 59 para 79
            sys.stdout.write(f"> {notif}".ljust(80)[:79] + "\n") 
            
        for _ in range(linhas_vazias):
            sys.stdout.write(" ".ljust(80) + "\n")
            
        sys.stdout.write("-" * 80 + "\n")
        
        sys.stdout.write("\0338")
        sys.stdout.flush()

def receber(sock):
    global item, lance, tempo, vencedor, running

    while running:
        try:
            msg = sock.recv(1024).decode()
            if not msg: break
            
            linhas = msg.strip().split("\n")

            for linha in linhas:
                if not linha.strip():
                    continue

                if "[LEILÃO INICIADO]" in linha or "[ITEM]:" in linha:
                    partes = linha.split("|")
                    if len(partes) >= 3:
                        item = partes[0].split(":")[1].strip()
                        lance = partes[1].split("R$")[1].strip()
                        quem = partes[2].split(":")[1].strip()
                        
                        vencedor = "VOCÊ" if quem != "anonimo" and quem != "nenhum" else ("Anônimo" if quem == "anonimo" else "Ninguém")

                elif "[TEMPO RESTANTE]" in linha:
                    tempo_recebido = linha.split(":")[1].strip()
                    tempo = str(tempo_recebido)

                elif "[ITEM VENDIDO]" in linha:
                    # Agora ele apenas avisa que vendeu e reseta o vencedor para o próximo
                    adicionar_notificacao(linha)
                    vencedor = "Aguardando próximo..."

                elif any(tag in linha for tag in ["[INFO]", "[RESPOSTA]", "[ALERTA]", "CONECTADO!!"]):
                    adicionar_notificacao(linha)

            if running:
                desenhar()

        except Exception:
            running = False
            break

def enviar(sock):
    global running

    limpar() 
    sys.stdout.write("\n" * 20) 
    sys.stdout.write("Digite seu lance ou comando:\n> ")
    sys.stdout.flush()

    desenhar()

    while running:
        try:
            msg = input()
            if not running: break
                
            sock.sendall((msg + "\n").encode())
            
            if msg == ":quit":
                running = False
                break
                
            sys.stdout.write("\033[1A\033[2K> ")
            sys.stdout.flush()
            
        except EOFError:
            break

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        
        # --- LOGIN ANTES DA TELA ---
        # Recebe o texto "Por favor, digite seu NOME DE USUARIO: " do servidor
        mensagem_login = client.recv(1024).decode() 
        nome = input(mensagem_login)
        client.sendall((nome + "\n").encode())
        
        # --- INICIA A INTERFACE ---
        thread_receber = threading.Thread(target=receber, args=(client,))
        thread_receber.daemon = True
        thread_receber.start()
        
        enviar(client)
        
    except ConnectionRefusedError:
        print("Erro: Servidor não encontrado. Ligue o servidor primeiro!")
    finally:
        client.close()