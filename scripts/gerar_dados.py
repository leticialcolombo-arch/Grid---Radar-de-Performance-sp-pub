"""Atualiza os dados embutidos no index.html do dashboard "Nodos com descarte".

Uso:
    python3 scripts/gerar_dados.py <general.xlsx> <Carteira.xlsx> [ano]

Regras:
- general.xlsx: "Fecha" e "Facility Nodo" vêm mescladas (só na 1ª linha do
  bloco), então são preenchidas para baixo. O bloco final com Fecha "*" é
  ignorado por não ter data.
- Carteira.xlsx: um nodo "não opera aos sábados" quando a coluna SÁBADO é "-".
  A coluna FACILITY pode trazer mais de um código ("BRDSP049 - BRNSP49").
- "Seg a sex, sem fim de semana": SÁBADO "-" e o texto do horário não cita
  sábado nem domingo.
- "Alto volume": média diária de Volumen Total (descarte) >= mediana da média
  diária de todos os nodos da base no ano.
- Entram os nodos da Carteira sem sábado que tenham Excede la capacidad > 0
  OU que sejam seg a sex, sem fim de semana, com alto volume.
"""

import json
import re
import sys
from pathlib import Path

import pandas as pd

EXCEDE = "Excede la capacidad"


def carregar_carteira(caminho):
    carteira = pd.read_excel(caminho)
    nodos = {}
    for _, linha in carteira.iterrows():
        for codigo in str(linha["FACILITY"]).split(" - "):
            codigo = codigo.strip()
            if codigo and codigo != "-":
                nodos[codigo] = {
                    "placeId": int(linha["PLACE ID"]),
                    "horario": str(linha["HORÁRIO DE FUNCIONAMENTO"]).strip(),
                    "sabado": str(linha["SÁBADO"]).strip(),
                }
    return nodos


def carregar_general(caminho, ano):
    base = pd.read_excel(caminho)
    base["Fecha"] = base["Fecha"].ffill()
    bloco = (base["Facility Nodo"].notna()).cumsum()
    base["Facility Nodo"] = base["Facility Nodo"].ffill()
    base["Tipo de Nodo"] = base.groupby(bloco)["Tipo de Nodo"].ffill()
    base = base[base["Fecha"] != "*"].copy()
    base["data"] = pd.to_datetime(base["Fecha"], format="%d/%m/%Y")
    return base[base["data"].dt.year == ano]


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    ano = int(sys.argv[3]) if len(sys.argv) > 3 else 2026
    carteira = carregar_carteira(sys.argv[2])
    base = carregar_general(sys.argv[1], ano)

    sem_sabado = {k: v for k, v in carteira.items() if v["sabado"] == "-"}
    diario = (
        base.groupby(["Facility Nodo", "Tipo de Nodo", "data"])
        .agg(exc=(EXCEDE, "sum"), vol=("Volumen Total", "sum"))
        .reset_index()
    )
    por_nodo = diario.groupby("Facility Nodo").agg(
        exc=("exc", "sum"), vol=("vol", "sum"), dias=("data", "nunique")
    )
    por_nodo["media_dia"] = por_nodo["vol"] / por_nodo["dias"]
    mediana_dia = float(por_nodo["media_dia"].median())

    for info in sem_sabado.values():
        info["segSex"] = not re.search(r"s[áa]bado|domingo", info["horario"], re.I)

    def entra(f):
        if f not in por_nodo.index:
            return False
        n = por_nodo.loc[f]
        alto = n["media_dia"] >= mediana_dia
        return n["exc"] > 0 or (sem_sabado[f]["segSex"] and alto)

    ofensores = [f for f in sem_sabado if entra(f)]

    alvo = diario[diario["Facility Nodo"].isin(ofensores)]
    dados = {
        "ano": ano,
        "periodo": [
            base["data"].min().strftime("%Y-%m-%d"),
            base["data"].max().strftime("%Y-%m-%d"),
        ],
        "medianaVolumeDia": round(mediana_dia, 1),
        "volumeBasePorMes": {
            str(mes): int(v)
            for mes, v in diario.groupby(diario["data"].dt.month)["vol"].sum().items()
        },
        "excedeBasePorMes": {
            str(mes): int(v)
            for mes, v in diario.groupby(diario["data"].dt.month)["exc"].sum().items()
        },
        "nodos": {
            f: {
                **sem_sabado[f],
                "tipo": alvo.loc[alvo["Facility Nodo"] == f, "Tipo de Nodo"].iloc[0],
                "altoVolume": bool(por_nodo.loc[f, "media_dia"] >= mediana_dia),
            }
            for f in ofensores
        },
        "diario": [
            [r["Facility Nodo"], r["data"].strftime("%Y-%m-%d"), int(r["exc"]), int(r["vol"])]
            for _, r in alvo.sort_values(["Facility Nodo", "data"]).iterrows()
        ],
    }
    # Os dados ficam embutidos no próprio HTML para a página abrir sozinha.
    saida = Path(__file__).resolve().parent.parent / "index.html"
    bloco = (
        '<script id="dados">/* Gerado por scripts/gerar_dados.py - não editar à mão. */\n'
        "window.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n</script>"
    )
    html, n = re.subn(
        r'<script id="dados">.*?</script>', lambda _: bloco, saida.read_text(encoding="utf-8"), flags=re.S
    )
    if n != 1:
        sys.exit('index.html sem o bloco <script id="dados">')
    saida.write_text(html, encoding="utf-8")
    print(f"{saida}: {len(ofensores)} nodos, {len(dados['diario'])} dias")

if __name__ == "__main__":
    main()
