# Leilão Online com Sockets e Threads — Fase 1 e Fase 2

## Descrição do Projeto

Este projeto implementa um **sistema de leilão online** desenvolvido em **Python**, utilizando comunicação em rede no modelo **cliente-servidor**.

O sistema evoluiu em duas fases:

- **Fase 1:** base de comunicação com um único cliente remoto, usando sockets TCP e threads para comunicação assíncrona e controle de tempo do leilão.
- **Fase 2:** suporte a múltiplos clientes simultâneos, controle de limite de conexões via linha de comando, sistema de saldo com bloqueio/desbloqueio, persistência de dados em memória e correções de bugs de concorrência.

---

## Fase 1 — Base do Sistema

### O que foi implementado

O servidor gerencia:

- Conexão com um cliente remoto
- Recebimento de lances em tempo real
- Controle de tempo do leilão
- Simulação de usuários anônimos
- Atualização de informações do leilão via comandos

---

## Fase 2 — Multi-usuário com Persistência

### O que foi implementado

- Suporte a **múltiplos clientes simultâneos**, cada um com threads dedicadas
- **Limite de conexões** configurável via argumento na linha de comando
- **Rejeição de conexões** quando o servidor está lotado, com mensagem de erro ao cliente
- **Sistema de identificação** de usuários por nome ao conectar
- **Banco de dados em memória** de usuários com saldo, itens e bloqueios
- **Novos usuários** começam com R$ 5.000,00 de crédito
- **Usuários recorrentes** recuperam saldo e itens ao reconectar
- **Lógica de bloqueio de saldo** ao dar lance, com desbloqueio correto em todos os cenários
- **Venda de itens** por 90% do valor pago via comando `:vender`
- **Broadcast de lances** para todos os clientes conectados em tempo real
- **Filas individuais de envio** por cliente para evitar conflito entre threads no socket

---

# Tecnologias Utilizadas

- **Python 3**
- **Sockets TCP (biblioteca `socket`)**
- **Threads (`threading`)**
- **Controle de concorrência (`threading.Lock`)**
- **Filas thread-safe (`queue.Queue`)**
- **Comunicação assíncrona cliente-servidor**
- **Argumentos de linha de comando (`sys.argv`)**

Bibliotecas utilizadas:

```python
socket
threading
time
random
queue
sys
datetime
```

---

# Como Executar

### Servidor

```bash
# Com limite de conexões definido (ex: 5 clientes simultâneos)
python server.py 5

# Sem argumento — usa o limite padrão de 3 clientes
python server.py
```

### Cliente

```bash
python client.py
```

---

# Arquitetura do Sistema

O sistema segue o modelo **Cliente ↔ Servidor**.

---

## Servidor

Responsável por:

- Gerenciar o estado global do leilão (item atual, lance, cronômetro)
- Validar e processar lances de múltiplos clientes
- Controlar o cronômetro regressivo por item
- Simular o bot anônimo de lances
- Gerenciar saldo, bloqueios e carteira de cada usuário
- Limitar e controlar conexões simultâneas

### Threads do Servidor

| Thread | Responsabilidade |
|---|---|
| `gerenciar_leiloes` | Controla a sequência de itens e o cronômetro regressivo |
| `simular_usuario` | Bot anônimo que gera lances aleatórios simulando concorrência |
| `processar_cliente` (Thread A — por cliente) | Recebe e processa comandos do cliente |
| `_thread_envio` (Thread B — por cliente) | Consome a fila individual e envia mensagens ao socket do cliente |

---

## Cliente

Responsável por:

- Identificar o usuário ao conectar (login por nome)
- Enviar comandos e lances ao servidor
- Receber atualizações em tempo real
- Exibir painel TUI com item, lance atual, vencedor, cronômetro e notificações

### Threads do Cliente

| Thread | Responsabilidade |
|---|---|
| Thread 1 | Ler entrada do usuário (`input`) e enviar ao servidor |
| Thread 2 | Receber mensagens do servidor e atualizar o painel |

---

# Comandos Disponíveis

| Comando | Descrição |
|---|---|
| `VALOR` | Dar um lance (ex: `1800`) |
| `:item` | Exibe o item atual e o maior lance |
| `:tempo` | Consulta o tempo restante do leilão |
| `:carteira` | Exibe saldo livre, valor bloqueado e itens comprados |
| `:vender NOME` | Vende um item por 90% do valor pago (ex: `:vender Nintendo Switch`) |
| `:quit` | Sai da aplicação |

---

# Lógica de Saldo e Bloqueio

| Evento | Comportamento |
|---|---|
| Novo usuário conecta | Recebe R$ 5.000,00 de crédito inicial |
| Usuário dá um lance | O valor do lance é bloqueado do saldo livre |
| Usuário é superado por outro | O valor bloqueado é devolvido ao saldo livre |
| Usuário aumenta o próprio lance | O bloqueio anterior é restaurado antes de aplicar o novo |
| Usuário vence o leilão | O valor bloqueado é debitado permanentemente e o item é creditado |
| Bot ou ninguém vence | Todos os saldos bloqueados são devolvidos a seus respectivos donos |

---

# Simulação do Bot Anônimo

O servidor executa uma thread de simulação que imita outros participantes no leilão:

- Gera lances com variação de **+1% a +3%** acima do lance atual (calibrado para ser vencível pelo usuário)
- Cada item recebe um **limite sorteado de 1 a 3 lances** do bot por rodada
- O bot aguarda entre **8 e 15 segundos** entre cada lance para dar tempo de reação ao usuário
- O bot **não age nos últimos 5 segundos** do cronômetro, preservando a chance de lance final humano
- Ao dar um lance, o bot **devolve o saldo bloqueado** do usuário humano que estava vencendo

---

# Problemas Enfrentados e Soluções

## Fase 1

### Concorrência entre Threads

Múltiplas threads acessavam as mesmas variáveis `lance_atual` e `tempo_restante`, gerando condições de corrida.

```python
lock = threading.Lock()

with lock:
    lance_atual = valor
```

### Conflito entre `input()` e `print()`

As threads do cliente imprimiam mensagens enquanto o usuário digitava, misturando saída no terminal.

Solução: controle de acesso ao terminal e reorganização do fluxo de leitura e escrita com escrita ANSI posicional.

### Bufferização do TCP

O protocolo TCP não preserva mensagens individuais — apenas um fluxo de bytes. Isso causava respostas agrupadas ou atrasadas.

Solução: uso de delimitador `\n` e leitura linha a linha no cliente.

### Encerramento incorreto de threads

Threads continuavam executando após o cliente sair.

```python
leilao_ativo = False
```

---

## Fase 2

### Bug: duplo incremento de `clientes_ativos`

A variável `clientes_ativos` era incrementada em dois lugares para a mesma conexão: dentro de `processar_cliente()` e no loop principal. Isso fazia cada cliente contar como dois, reduzindo o limite efetivo à metade.

Solução: remover o incremento de dentro de `processar_cliente()`, mantendo apenas o controle no loop principal.

### Bug: bot anônimo sempre vencia o leilão

O bot dava lances com variação de até +8% e tinha limite fixo de participações, tornando impossível para o usuário humano vencer consistentemente.

Solução: variação reduzida para +1% a +3%, limite de lances sorteado por item entre 1 e 3, intervalo maior entre lances e bloqueio de ação nos últimos 5 segundos do cronômetro.

### Bug: painel exibia "VOCÊ" para todos os clientes

O client.py substituía qualquer nome de vencedor por "VOCÊ" independentemente de qual usuário estava liderando, fazendo todos os clientes conectados verem a mesma mensagem incorreta.

Solução: armazenar o nome do usuário local em `meu_nome` e exibir "VOCÊ (nome)" apenas quando o nome recebido do servidor corresponde ao usuário local. Para os demais clientes, exibe o nome real do vencedor.

### Conflito de escrita simultânea no socket

Com múltiplas threads escrevendo no socket do mesmo cliente (Thread A de comandos e `enviar_para_todos`), havia risco de dados corrompidos ou exceções de concorrência.

Solução: criação de uma fila individual por cliente usando `queue.Queue`. Toda escrita passa pela fila, consumida exclusivamente pela Thread B (`_thread_envio`), garantindo acesso serial ao socket.

### Bloqueio de saldo não era devolvido quando bot vencia

Quando o bot ou ninguém vencia um item, o saldo bloqueado dos usuários humanos que tinham dado lances permanecia bloqueado indefinidamente.

Solução: ao encerrar um item sem vencedor humano, o servidor itera `usuarios_db` e devolve todo saldo bloqueado maior que zero, notificando cada usuário afetado via sua fila individual.

---

# Estrutura de Arquivos

```
├── server.py   # Servidor TCP com gerenciamento de leilão e múltiplos clientes
├── client.py   # Cliente TCP com interface TUI em terminal
└── README.md   # Documentação do projeto
```
