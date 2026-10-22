"""Analise de sensibilidade da classificacao DORA (RQ 07).

O mesmo repositorio e classificado (Elite / High / Medium / Low) sob tres
combinacoes de definicoes operacionais, as do exemplo do enunciado:

| Combinacao      | Unidade de deploy     | Lead time | CFR |
| --------------- | --------------------- | --------- | --- |
| C1 (referencia) | release               | (a)       | (a) |
| C2              | release + pre-release | (b)       | (b) |
| C3              | tag                   | (b)       | (a) |

O tempo de recuperacao vem dos workflow runs e nao depende da unidade de
deploy: e o mesmo nas tres. Para cada par de combinacoes, mede-se a % de
repositorios que mudam de categoria e o kappa de Cohen ponderado (linear), que
pesa uma troca Elite -> High menos que Elite -> Low, porque as categorias sao
ordenadas. So entram no par os repositorios classificados nas duas combinacoes.
"""

from __future__ import annotations

import math

from sklearn.metrics import cohen_kappa_score

from metricas.classificacao import PONTOS, classificar_repositorio

# Combinacao -> colunas do dataset (frequencia, lead time, CFR, recuperacao).
COMBINACOES = {
    "C1": ("deployment_frequency", "lead_time_release_dias", "cfr_ci", "tempo_recuperacao_horas"),
    "C2": ("deployment_frequency_pre", "lead_time_commit_dias_pre", "cfr_entrega_pre", "tempo_recuperacao_horas"),
    "C3": ("deployment_frequency_tag", "lead_time_commit_dias_tag", "cfr_ci", "tempo_recuperacao_horas"),
}

DESCRICAO_COMBINACOES = {
    "C1": "release, lead time (a), CFR (a)",
    "C2": "release + pre-release, lead time (b), CFR (b)",
    "C3": "tag, lead time (b), CFR (a)",
}

PARES = [("C1", "C2"), ("C1", "C3"), ("C2", "C3")]


def _float_ou_none(valor) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def classificar_combinacao(linha: dict, combinacao: str) -> dict:
    """Categorias de um repositorio (linha do dataset) sob a combinacao dada."""
    return classificar_repositorio(*(_float_ou_none(linha.get(c)) for c in COMBINACOES[combinacao]))


def comparar_classificacoes(categorias_x: list[str | None], categorias_y: list[str | None]) -> dict:
    """% de mudanca de categoria e kappa ponderado linear entre duas classificacoes.

    As listas sao alinhadas por repositorio; pares com alguma categoria ausente
    ficam de fora. `kappa` e None quando nao ha pares suficientes ou quando o
    kappa nao esta definido (ex.: todos na mesma categoria nas duas).
    """
    pares = [(x, y) for x, y in zip(categorias_x, categorias_y) if x is not None and y is not None]
    n = len(pares)
    if n == 0:
        return {"n": 0, "mudaram": 0, "pct_mudaram": None, "kappa": None}

    mudaram = sum(1 for x, y in pares if x != y)
    kappa = None
    # Com uma unica categoria nas duas classificacoes, o kappa e 0/0 (indefinido).
    if n >= 2 and len({c for par in pares for c in par}) > 1:
        valor = cohen_kappa_score(
            [PONTOS[x] for x, _ in pares], [PONTOS[y] for _, y in pares], labels=[1, 2, 3, 4], weights="linear"
        )
        kappa = None if math.isnan(valor) else float(valor)
    return {"n": n, "mudaram": mudaram, "pct_mudaram": mudaram / n, "kappa": kappa}


def interpretar_kappa(kappa: float | None) -> str | None:
    """Concordancia segundo Landis & Koch (1977)."""
    if kappa is None:
        return None
    if kappa < 0:
        return "pobre"
    if kappa <= 0.20:
        return "leve"
    if kappa <= 0.40:
        return "razoavel"
    if kappa <= 0.60:
        return "moderada"
    if kappa <= 0.80:
        return "substancial"
    return "quase perfeita"
