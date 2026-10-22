"""RQ 06 - caracteristicas dos repositorios associadas ao desempenho DORA.

Le o CSV final da amostra e compara as metricas DORA (RQ 01 a RQ 04) entre
subgrupos de repositorios, para os fatores: linguagem principal, popularidade
(quartis de estrelas), numero de contribuidores (quartis) e idade do
repositorio (quartis). O fator "tipo do projeto" (rotulado manualmente na
amostra-ouro, secao 6) nao esta aqui porque so existe para os 60 repositorios
rotulados, nao para a amostra inteira.

Uso:
    python -m analise.rq06 --entrada resultados/amostra_metricas.csv

O CSV de entrada precisa ter, por repositorio, as colunas:
    language, stargazers_count, n_contribuidores, idade_dias   (fatores)
    deployment_frequency, cfr_ci, lead_time_release_dias,
    tempo_recuperacao_horas                                   (metricas DORA)
"""

from __future__ import annotations

import argparse
import csv

from metricas.subgrupos import agrupar_por_grupo, comparar_grupos, corrigir_holm, quartis

METRICAS = {
    "deployment_frequency": "deployment_frequency",
    "cfr": "cfr_ci",
    "lead_time": "lead_time_release_dias",
    "tempo_recuperacao": "tempo_recuperacao_horas",
}

FATORES_NUMERICOS = {
    "popularidade": "stargazers_count",
    "contribuidores": "n_contribuidores",
    "idade": "idade_dias",
}


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def carregar_repositorios(caminho_csv: str) -> list[dict]:
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def _grupos_do_fator(repositorios: list[dict], fator: str) -> list:
    if fator == "linguagem":
        return [linha.get("language") for linha in repositorios]

    coluna = FATORES_NUMERICOS[fator]
    valores = [_float_ou_none(linha.get(coluna)) for linha in repositorios]
    # quartis() exige lista sem None: repos sem o fator ficam de fora do agrupamento
    indices_validos = [i for i, v in enumerate(valores) if v is not None]
    grupos_validos = quartis([valores[i] for i in indices_validos])
    grupos: list = [None] * len(valores)
    for posicao, indice in enumerate(indices_validos):
        grupos[indice] = f"Q{grupos_validos[posicao]}"
    return grupos


def calcular_rq06(repositorios: list[dict]) -> list[dict]:
    """Um resultado por combinacao fator x metrica, ja com p-valor corrigido (Holm)."""
    fatores = ["linguagem", "popularidade", "contribuidores", "idade"]
    resultados = []

    for fator in fatores:
        grupos_do_fator = _grupos_do_fator(repositorios, fator)
        for nome_metrica, coluna_metrica in METRICAS.items():
            valores_metrica = [_float_ou_none(linha.get(coluna_metrica)) for linha in repositorios]
            grupos = agrupar_por_grupo(valores_metrica, grupos_do_fator)
            comparacao = comparar_grupos(grupos)
            resultados.append({"fator": fator, "metrica": nome_metrica, **comparacao})

    return corrigir_holm(resultados)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    args = parser.parse_args()

    repositorios = carregar_repositorios(args.entrada)
    for resultado in calcular_rq06(repositorios):
        print(
            f"{resultado['fator']} x {resultado['metrica']}: "
            f"{resultado['teste']} p_corrigido={resultado.get('p_valor_corrigido')} "
            f"efeito={resultado.get('efeito')} significativo={resultado.get('significativo')}"
        )


if __name__ == "__main__":
    main()
