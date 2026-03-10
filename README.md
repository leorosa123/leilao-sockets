#  Leilão Online com Sockets e Threads — Fase 1

## Descrição do Projeto

Este projeto implementa a **primeira fase de um sistema de leilão online** desenvolvido em **Python**, utilizando comunicação em rede no modelo **cliente-servidor**.

O objetivo desta etapa é criar a base de comunicação entre cliente e servidor utilizando **sockets TCP**, além de implementar **processamento concorrente com threads** para permitir comunicação assíncrona e controle do tempo do leilão.

Nesta fase, o servidor gerencia:

* Conexão com um cliente remoto
* Recebimento de lances em tempo real
* Controle de tempo do leilão
* Simulação de usuários anônimos
* Atualização de informações do leilão via comandos

---

#  Tecnologias Utilizadas

* **Python 3**
* **Sockets TCP (biblioteca `socket`)**
* **Threads (`threading`)**
* **Controle de concorrência (`threading.Lock`)**
* **Comunicação assíncrona cliente-servidor**

Bibliotecas utilizadas:

```python
socket
threading
time
random
```

---

# Arquitetura do Sistema

O sistema segue o modelo **Cliente ↔ Servidor**.

## Servidor

Responsável por:

* Gerenciar o estado do leilão
* Validar lances
* Controlar o cronômetro
* Simular usuários anônimos

Threads utilizadas:

| Thread   | Responsabilidade                            |
| -------- | ------------------------------------------- |
| Thread 1 | Receber comandos e lances do cliente        |
| Thread 2 | Controlar o cronômetro do leilão            |
| Thread 3 | Simular usuários anônimos realizando lances |

---

## Cliente

Responsável por:

* Enviar comandos e lances ao servidor
* Receber atualizações em tempo real

Threads utilizadas:

| Thread   | Responsabilidade                 |
| -------- | -------------------------------- |
| Thread 1 | Ler entrada do usuário (`input`) |
| Thread 2 | Receber mensagens do servidor    |

---

# Simulação de Usuários Anônimos

Para simular múltiplos participantes no leilão, o servidor executa uma **thread de simulação** que:

* gera lances aleatórios
* valores ligeiramente maiores ou menores que o atual
* executa **até 4 vezes**
* reinicia o cronômetro se o lance for válido

# Problemas Enfrentados Durante o Desenvolvimento

Durante a implementação foram identificados alguns desafios comuns em sistemas concorrentes e distribuídos.

##  Concorrência entre Threads

Múltiplas threads acessavam as mesmas variáveis:

* `lance_atual`
* `tempo_restante`

Isso gerava **condições de corrida (race condition)**.

Solução aplicada:

```python
lock = threading.Lock()

with lock:
    lance_atual = valor
```

---

## Conflito entre `input()` e `print()`

As threads do cliente imprimiam mensagens enquanto o usuário digitava.

Resultado:

```
mensagens misturadas no terminal
```

Solução:

* controle de acesso ao terminal
* reorganização do fluxo de leitura e escrita

---

##  Bufferização do TCP

O protocolo TCP não preserva mensagens individuais, apenas um **fluxo de bytes**.

Isso causava:

* respostas atrasadas
* múltiplas mensagens agrupadas

Solução:

* uso de delimitador `\n`
* leitura com buffer no cliente

---

## Encerramento incorreto de threads

Algumas threads continuavam executando após o cliente sair.

Solução:

uso de variável de controle:

```python
leilao_ativo = False
```

---

#  Próximas Etapas do Projeto

Próximas melhorias previstas:

* suporte a **múltiplos clientes simultâneos**

---
