"""Correlacao entre deployment frequency e change failure rate (RQ 05).

RQ 05 pergunta se repositorios com maior frequencia de deploy (RQ 01)
apresentam maior ou menor taxa de falha (RQ 03, CFR). A correlacao usada e a
de Spearman (`scipy.stats.spearmanr`), calculada sobre o *ranking* dos
valores, nao sobre os valores brutos - por isso nao exige distribuicao normal
nem relacao linear entre as duas metricas.

Cada repositorio e representado por um dicionario:

    {
        "full_name": "owner/repo",
        "deployment_frequency": 0.45,   # releases por semana (RQ 01)
        "cfr": 0.2,                     # change failure rate, variante (a) ou (b) (RQ 03)
    }

O CFR e calculado em duas variantes (RQ 03 a e b); `spearman_frequencia_cfr`
deve ser chamada uma vez para cada variante, passando a chave correspondente
em `chave_cfr`.
"""

from __future__ import annotations

from scipy.stats import spearmanr


def _pares_validos(repositorios: list[dict], chave_cfr: str) -> tuple[list[float], list[float]]:
    """Extrai (frequencias, cfrs), descartando repositorios sem um dos dois valores.

    Faltar deployment frequency ou CFR e uma situacao esperada (ex.: CFR (b)
    sem releases avaliaveis por censura), por isso o par inteiro e descartado
    em vez de levantar erro.
    """
    frequencias = []
    cfrs = []
    for repo in repositorios:
        frequencia = repo.get("deployment_frequency")
        cfr = repo.get(chave_cfr)
        if frequencia is None or cfr is None:
            continue
        frequencias.append(frequencia)
        cfrs.append(cfr)
    return frequencias, cfrs


def spearman_frequencia_cfr(repositorios: list[dict], chave_cfr: str = "cfr") -> dict:
    """Correlacao de Spearman entre deployment frequency e CFR.

    `chave_cfr` seleciona qual variante do CFR (RQ 03) entra na correlacao -
    normalmente `"cfr_ci"` para a variante (a) ou `"cfr_entrega"` para a (b).
    Repositorios sem um dos dois valores sao ignorados (par incompleto).

    Devolve rho, p-valor e n; `rho` e `p_valor` sao `None` quando restam menos
    de 2 pares validos, caso em que a correlacao nao pode ser calculada.
    """
    frequencias, cfrs = _pares_validos(repositorios, chave_cfr)
    n = len(frequencias)
    if n < 2:
        return {"rho": None, "p_valor": None, "n": n}

    resultado = spearmanr(frequencias, cfrs)
    return {"rho": resultado.statistic, "p_valor": resultado.pvalue, "n": n}
