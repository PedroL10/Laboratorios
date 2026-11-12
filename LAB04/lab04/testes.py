"""Aplica os dois testes de hipótese (t de Welch e Mann-Whitney) a dados simulados."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from lab04.config import ALFA, N_SIMULACOES, criar_rng
from lab04.simulacao import gerar_pares, gerar_simulados_por_grupo

RAIZ = Path(__file__).parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"


def aplicar_welch(sem_bot, com_bot) -> dict:
    """Aplica o teste t de Welch (variâncias desiguais) e retorna estatística, graus de liberdade e p-valor."""
    resultado = stats.ttest_ind(sem_bot, com_bot, equal_var=False)
    return {
        "teste": "welch",
        "estatistica": resultado.statistic,
        "graus_liberdade": resultado.df,
        "estatistica_padronizada": resultado.statistic,
        "p_valor": resultado.pvalue,
    }


def aplicar_mannwhitney(sem_bot, com_bot) -> dict:
    """Aplica o teste de Mann-Whitney e retorna U, sua versão padronizada (z) e o p-valor.

    U conta os pares (PR sem bot, PR com bot) em que o PR sem bot demorou mais. Sob H0, U
    tem média n1·n2/2, e o z mede quantos desvios padrão U está longe dessa média.
    """
    resultado = stats.mannwhitneyu(sem_bot, com_bot, alternative="two-sided")
    n1, n2 = len(sem_bot), len(com_bot)
    z = (resultado.statistic - n1 * n2 / 2) / np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return {
        "teste": "mann_whitney",
        "estatistica": resultado.statistic,
        "graus_liberdade": np.nan,
        "estatistica_padronizada": z,
        "p_valor": resultado.pvalue,
    }


def interpretar(resultado: dict, alfa: float = ALFA) -> str:
    """Descreve em uma frase se o teste rejeitou H0 ao nível alfa."""
    nome = resultado["teste"].replace("_", " ")
    situacao = "rejeita H0 (há diferença entre os grupos)"
    if resultado["p_valor"] >= alfa:
        situacao = "não rejeita H0 (sem evidência de diferença entre os grupos)"
    return f"{nome}: p-valor={resultado['p_valor']:.4f}, alfa={alfa} -> {situacao}."


def explicar(resultado: dict, sem_bot, com_bot, alfa: float = ALFA) -> str:
    """Explica o resultado em linguagem simples: o que o teste comparou, em que direção e a decisão."""
    p = resultado["p_valor"]
    decisao = (
        f"Como p = {p:.4f} < {alfa}, o teste rejeita H₀."
        if p < alfa
        else f"Como p = {p:.4f} ≥ {alfa}, o teste não rejeita H₀."
    )
    if resultado["teste"] == "welch":
        comparacao = (
            f"O t de Welch compara as médias: {np.mean(sem_bot):.1f} h sem bot e "
            f"{np.mean(com_bot):.1f} h com bot (t = {resultado['estatistica']:.2f})."
        )
    else:
        chance = resultado["estatistica"] / (len(sem_bot) * len(com_bot))
        comparacao = (
            f"O Mann-Whitney compara as posições dos tempos ordenados: um PR sem bot demorou "
            f"mais que um PR com bot em {chance:.0%} dos pares, contra 50% esperados sob H₀ "
            f"(U = {resultado['estatistica']:.0f})."
        )
    return f"{comparacao} {decisao}"


def taxas_rejeicao(
    distribuicao,
    parametros: tuple,
    n: int,
    fator_efeito: float,
    rng: np.random.Generator,
    n_simulacoes: int = N_SIMULACOES,
) -> dict[str, float]:
    """Aplica os dois testes a n_simulacoes pares gerados e retorna a proporção de rejeições.

    Com fator 1, H0 é verdadeira e a proporção é o erro tipo I; com fator maior que 1, é o
    poder. Os pares são testados de uma vez (um por linha), sem laço em Python.
    """
    grupo_a, grupo_b = gerar_pares(distribuicao, parametros, n, fator_efeito, rng, n_simulacoes)
    p_welch = stats.ttest_ind(grupo_a, grupo_b, axis=1, equal_var=False).pvalue
    p_mann_whitney = stats.mannwhitneyu(grupo_a, grupo_b, axis=1, alternative="two-sided").pvalue
    return {
        "welch": float(np.mean(p_welch < ALFA)),
        "mann_whitney": float(np.mean(p_mann_whitney < ALFA)),
    }


def comparar_testes(rng) -> tuple[pd.DataFrame, list[str]]:
    """Gera um conjunto simulado, aplica os dois testes e salva o resultado em resultados/."""
    simulados = gerar_simulados_por_grupo(rng)
    sem_bot, com_bot = simulados["sem_bot"], simulados["com_bot"]
    resultados = [aplicar_welch(sem_bot, com_bot), aplicar_mannwhitney(sem_bot, com_bot)]

    tabela = pd.DataFrame(resultados)
    tabela["rejeita_h0"] = tabela["p_valor"] < ALFA
    tabela["interpretacao"] = [explicar(r, sem_bot, com_bot) for r in resultados]
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    tabela.to_csv(PASTA_RESULTADOS / "testes_exemplo.csv", index=False, float_format="%.4f")

    pd.DataFrame(simulados).to_csv(
        PASTA_RESULTADOS / "dados_simulados_exemplo.csv", index=False, float_format="%.2f"
    )

    interpretacoes = [interpretar(r) for r in resultados]
    return tabela, interpretacoes


def main() -> None:
    tabela, _ = comparar_testes(criar_rng())
    for linha in tabela["interpretacao"]:
        print(linha)


if __name__ == "__main__":
    main()
