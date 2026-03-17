import socket
import threading
import os
import sys

HOST = "127.0.0.1"
PORT = 5000

item = "Aguardando..."
lance = "0.00"
tempo = "20"
vencedor = "Ninguém" # <--- Nova variável
running = True

lock = threading.Lock()

if os.name == 'nt':
    os.system("")

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def desenhar():
    with lock:
        sys.stdout.write("\0337\033[H") 
        
        sys.stdout.write(f"Item: {item:<30}\n")
        sys.stdout.write(f"Lance atual: R$ {lance:<25}\n")
        sys.stdout.write(f"Vencendo agora: {vencedor:<25}\n") # <--- Mostra quem tá ganhando
        sys.stdout.write(f"Tempo restante: {tempo:<25}\n")
        sys.stdout.write("-" * 40 + "\n")
        
        sys.stdout.write("\0338")
        sys.stdout.flush()

def receber(sock):
    global item, lance, tempo, vencedor, running

    while running:
        try:
            msg = sock.recv(1024).decode()
            if not msg: break
            
            linhas = msg.strip().split("\n")

            with lock:
                for linha in linhas:
                    if "[LEILÃO INICIADO]" in linha or "[ITEM]" in linha:
                        partes = linha.split("|")
                        if len(partes) >= 3:
                            item = partes[0].split(":")[1].strip()
                            lance = partes[1].split("R$")[1].strip()
                            quem = partes[2].split(":")[1].strip()
                            
                            # Traduz quem está ganhando para ficar mais visual
                            if quem == "cliente":
                                vencedor = "VOCÊ"
                            elif quem == "anonimo":
                                vencedor = "Anônimo"
                            else:
                                vencedor = "Ninguém"

                    elif "[TEMPO RESTANTE]" in linha:
                        tempo_recebido = int(linha.split(":")[1].strip())
                        
                        tempo = str(tempo_recebido)

                    elif "[ITEM VENDIDO]" in linha:
                        limpar()
                        print("\n" + linha)
                        print("Pressione ENTER para sair...")
                        running = False
                        return

            if running:
                desenhar()

        except Exception:
            running = False
            break

def enviar(sock):
    global running

    limpar()
    print("\n\n\n\n\n") 
    print("Digite seu lance (ou ':quit' para sair): ")

    while running:
        try:
            msg = input()
            if not running: break
                
            sock.sendall((msg + "\n").encode())
            if msg == ":quit":
                running = False
                break
                
            sys.stdout.write("\033[1A\033[2K")
            sys.stdout.flush()
            
        except EOFError:
            break

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        thread_receber = threading.Thread(target=receber, args=(client,))
        thread_receber.daemon = True
        thread_receber.start()
        enviar(client)
    except ConnectionRefusedError:
        print("Erro: Servidor não encontrado.")
    finally:
        client.close()