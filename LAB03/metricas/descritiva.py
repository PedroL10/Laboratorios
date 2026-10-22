"""Estatistica descritiva das metricas (RQ 01 a 04).

O enunciado pede mediana e IQR (intervalo interquartil), e nao media e
desvio-padrao: metricas de repositorios costumam ter distribuicoes muito
assimetricas, e a media e puxada pelos poucos repositorios extremos.

Os quartis usam interpolacao linear entre as posicoes ordenadas
(`statistics.quantiles(method="inclusive")`), o mesmo padrao do numpy e do pandas.
"""

from __future__ import annotations

import statistics

from metricas.classificacao import ELITE, HIGH, LOW, MEDIUM

CATEGORIAS = [ELITE, HIGH, MEDIUM, LOW]


def resumo(valores: list[float | None]) -> dict:
    """n, mediana, Q1, Q3, IQR, minimo e maximo dos valores presentes (None e ignorado)."""
    presentes = sorted(v for v in valores if v is not None)
    n = len(presentes)
    if n == 0:
        return {"n": 0, "mediana": None, "q1": None, "q3": None, "iqr": None, "minimo": None, "maximo": None}
    if n == 1:
        q1 = q3 = presentes[0]
    else:
        q1, _, q3 = statistics.quantiles(presentes, n=4, method="inclusive")
    return {
        "n": n,
        "mediana": statistics.median(presentes),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "minimo": presentes[0],
        "maximo": presentes[-1],
    }


def distribuicao_categorias(categorias: list[str | None]) -> dict:
    """Quantos repositorios (e que proporcao dos classificados) em cada categoria DORA.

    `sem_categoria` conta os repositorios sem valor para a metrica; eles ficam
    fora do denominador das proporcoes.
    """
    contagem = {c: 0 for c in CATEGORIAS}
    sem_categoria = 0
    for categoria in categorias:
        if categoria in contagem:
            contagem[categoria] += 1
        else:
            sem_categoria += 1
    classificados = sum(contagem.values())
    return {
        "contagem": contagem,
        "proporcao": {c: (n / classificados if classificados else None) for c, n in contagem.items()},
        "classificados": classificados,
        "sem_categoria": sem_categoria,
    }
