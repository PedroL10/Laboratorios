"""RQ 05 - correlacao entre deployment frequency e change failure rate.

Le o CSV final da amostra (RQ 01 a RQ 04 ja calculadas por repositorio) e
reporta a correlacao de Spearman entre deployment frequency e CFR, separada
para as duas variantes do CFR (a: proxy de CI, b: proxy de entrega).

Uso:
    python -m analise.rq05 --entrada resultados/amostra_metricas.csv

O CSV de entrada precisa ter, por repositorio, as colunas:
    deployment_frequency  (RQ 01, releases por semana)
    cfr_ci                (RQ 03 variante a, proxy de CI)
    cfr_entrega           (RQ 03 variante b, proxy de entrega)
Repositorios sem um desses valores sao ignorados em cada correlacao
(ver `metricas.correlacao.spearman_frequencia_cfr`).
"""

from __future__ import annotations

import argparse
import csv

from metricas.correlacao import spearman_frequencia_cfr

VARIANTES_CFR = {"a": "cfr_ci", "b": "cfr_entrega"}


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def carregar_repositorios(caminho_csv: str) -> list[dict]:
    """Le o CSV final e devolve os campos numericos usados pela RQ 05."""
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            {
                "full_name": linha.get("full_name"),
                "deployment_frequency": _float_ou_none(linha.get("deployment_frequency")),
                "cfr_ci": _float_ou_none(linha.get("cfr_ci")),
                "cfr_entrega": _float_ou_none(linha.get("cfr_entrega")),
            }
            for linha in leitor
        ]


def calcular_rq05(repositorios: list[dict]) -> dict:
    """Correlacao de Spearman entre deployment frequency e CFR, nas 2 variantes."""
    return {
        letra: spearman_frequencia_cfr(repositorios, chave_cfr=chave)
        for letra, chave in VARIANTES_CFR.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    args = parser.parse_args()

    repositorios = carregar_repositorios(args.entrada)
    resultado = calcular_rq05(repositorios)

    for letra, valores in resultado.items():
        print(f"CFR variante ({letra}): rho={valores['rho']} p={valores['p_valor']} n={valores['n']}")


if __name__ == "__main__":
    main()
