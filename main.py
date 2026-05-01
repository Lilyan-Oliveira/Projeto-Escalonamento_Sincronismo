import threading
import random
import time
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ranking = []
estado = []
tempos_execucao = {}
tempo_espera_hidratacao = {}

ordem_hidratacao = []
ordem_chegada_hidratacao = []

lock_hidratacao = threading.Lock()
fila_hidratacao = []
fila_lock = threading.Lock()

DISTANCIA_TOTAL = 200
PONTO_HIDRATACAO = 100
qtd = 10

tempos_hidratacao = {
    "Corredor 1": 0.5,
    "Corredor 2": 1.0,
    "Corredor 3": 0.8,
    "Corredor 4": 1.2,
    "Corredor 5": 0.6,
    "Corredor 6": 1.5,
    "Corredor 7": 0.7,
    "Corredor 8": 1.1,
    "Corredor 9": 0.4,
    "Corredor 10": 0.9
}

# escolha do algoritmo
while True:
    print("Escolha o algoritmo de hidratação:")
    print("1 - FCFS")
    print("2 - SJF")

    opcao = input("Digite 1 ou 2: ")

    if opcao == "1":
        ALGORITMO = "FCFS"
        break
    elif opcao == "2":
        ALGORITMO = "SJF"
        break
    else:
        print("Opção inválida!\n")

def barra(dist, tamanho=30):
    progresso = int((dist / DISTANCIA_TOTAL) * tamanho)
    pos_hidratacao = int((PONTO_HIDRATACAO / DISTANCIA_TOTAL) * tamanho)

    barra_str = ""
    for i in range(tamanho):
        if i == pos_hidratacao:
            barra_str += "|"
        elif i < progresso:
            barra_str += "█"
        else:
            barra_str += "-"
    return barra_str

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def corredor(id, nome):
    inicio = time.time()
    distancia = 0
    hidratou = False

    tempo_hidratacao = tempos_hidratacao[nome]

    while distancia < DISTANCIA_TOTAL:
        passo = random.randint(1, 10)

        evento = random.random()
        msg = ""

        if evento < 0.2:
            msg = "⚠️ Tropeçou"
            passo = 0
        elif evento < 0.35:
            msg = "🚀 Acelerou"
            passo *= 2

        distancia += passo
        distancia = min(distancia, DISTANCIA_TOTAL)

        # 💧 HIDRATAÇÃO
        if distancia >= PONTO_HIDRATACAO and not hidratou:
            msg = "💧 Chegou na hidratação"

            with fila_lock:
                ordem_chegada_hidratacao.append(nome)
                fila_hidratacao.append((nome, tempo_hidratacao))

                if ALGORITMO == "SJF":
                    fila_hidratacao.sort(key=lambda x: x[1])

            tempo_entrada = time.time()

            while True:
                with fila_lock:
                    if fila_hidratacao[0][0] == nome:
                        break
                estado[id] = (nome, distancia, "⏳ Esperando para hidratar")
                time.sleep(0.05)

            tempo_saida = time.time()
            tempo_espera_hidratacao[nome] = tempo_saida - tempo_entrada

            # região crítica
            with lock_hidratacao:
                inicio_hidratacao = time.time()

                while True:
                    tempo_passado = time.time() - inicio_hidratacao
                    restante = tempo_hidratacao - tempo_passado

                    if restante <= 0:
                        break

                    estado[id] = (nome, distancia, f"💧 Hidratando ({restante:.1f}s)")
                    time.sleep(0.1)

            with fila_lock:
                fila_hidratacao.pop(0)
                ordem_hidratacao.append(nome)

            estado[id] = (nome, distancia, "🏃‍♂️ Voltando a correr")

            hidratou = True

        estado[id] = (nome, distancia, msg)
        time.sleep(random.uniform(0.2, 0.6))

    tempos_execucao[nome] = time.time() - inicio
    ranking.append(nome)

def painel(nomes):
    while len(ranking) < len(nomes):
        limpar()
        print(f"🏁 CORRIDA ({ALGORITMO})\n")

        for nome, dist, msg in estado:
            print(f"{nome:12} |{barra(dist)}| {dist:3d}m {msg}")

        print("\nFila:", [n for n, _ in fila_hidratacao])
        time.sleep(0.1)

# iniciar
nomes = [f"Corredor {i+1}" for i in range(qtd)]
estado = [(nome, 0, "") for nome in nomes]

threads = []
for i, nome in enumerate(nomes):
    t = threading.Thread(target=corredor, args=(i, nome))
    threads.append(t)
    t.start()

painel_thread = threading.Thread(target=painel, args=(nomes,))
painel_thread.start()

for t in threads:
    t.join()

painel_thread.join()

# RESULTADOS
print("\n🏆 ORDEM FINAL:")
for i, nome in enumerate(ranking):
    print(f"{i+1}º {nome}")

print("\n📥 CHEGADA NA HIDRATAÇÃO:")
for i, nome in enumerate(ordem_chegada_hidratacao):
    print(f"{i+1}º {nome}")

print("\n💧 ORDEM DE HIDRATAÇÃO:")
for i, nome in enumerate(ordem_hidratacao):
    print(f"{i+1}º {nome}")

print("\n⏱️ TEMPO DE ESPERA:")
ordenado = sorted(tempo_espera_hidratacao.items(), key=lambda x: x[1])

for nome, tempo in ordenado:
    print(f"{nome:12} → {tempo:.2f}s")

media = sum(tempo_espera_hidratacao.values()) / len(tempo_espera_hidratacao)
print(f"\n📊 Média: {media:.2f}s")

# gráficos
def plot_graficos():
    import numpy as np

    ordem_fixa = sorted(nomes, key=lambda x: int(x.split()[1]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 🔹 GANTT
    timeline = {}
    tempo_atual = 0

    for nome in ordem_hidratacao:
        duracao = tempos_hidratacao[nome]
        timeline[nome] = (tempo_atual, duracao)
        tempo_atual += duracao

    for nome in ordem_fixa:
        espera = tempo_espera_hidratacao.get(nome, 0)

        if nome in timeline:
            inicio_exec, duracao = timeline[nome]

            # CINZA → espera
            ax1.barh(
                nome,
                espera,
                left=inicio_exec - espera,
                color="lightgray"
            )

            # AZUL → hidratação
            ax1.barh(
                nome,
                duracao,
                left=inicio_exec,
                color="tab:blue"
            )

        else:
            ax1.barh(nome, 0)

    ax1.set_axisbelow(True)

    max_tempo = max([inicio + dur for inicio, dur in timeline.values()])
    ticks = np.arange(0, max_tempo + 1, 1)

    ax1.set_xticks(ticks)
    ax1.xaxis.grid(True, linestyle='--', linewidth=1)

    ax1.set_title(f"Linha do Tempo ({ALGORITMO})")
    ax1.set_xlabel("Tempo (s)")

    legenda = [
        Patch(facecolor="lightgray", label="Tempo de Espera"),
        Patch(facecolor="tab:blue", label="Hidratação")
    ]

    ax1.legend(handles=legenda)

    valores = [tempo_espera_hidratacao.get(n, 0) for n in ordem_fixa]

    ax2.barh(ordem_fixa, valores, color="tab:blue")
    ax2.set_title("Tempo de Espera (Ordem dos Corredores)")
    ax2.set_xlabel("Segundos")

    plt.tight_layout()
    plt.show()

plot_graficos()