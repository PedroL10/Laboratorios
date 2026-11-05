"""Aplica os dois testes de hipótese (t de Welch e Mann-Whitney) a um conjunto simulado."""

from pathlib import Path

import pandas as pd
from scipy import stats

from lab04.config import ALFA, criar_rng
from lab04.simulacao import gerar_simulados_por_grupo

RAIZ = Path(__file__).parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"


def aplicar_welch(sem_bot, com_bot) -> dict:
    """Aplica o teste t de Welch (variâncias desiguais) e retorna estatística e p-valor."""
    resultado = stats.ttest_ind(sem_bot, com_bot, equal_var=False)
    return {"teste": "welch", "estatistica": resultado.statistic, "p_valor": resultado.pvalue}


def aplicar_mannwhitney(sem_bot, com_bot) -> dict:
    """Aplica o teste de Mann-Whitney e retorna estatística e p-valor."""
    resultado = stats.mannwhitneyu(sem_bot, com_bot, alternative="two-sided")
    return {"teste": "mann_whitney", "estatistica": resultado.statistic, "p_valor": resultado.pvalue}


def interpretar(resultado: dict, alfa: float = ALFA) -> str:
    """Descreve em uma frase se o teste rejeitou H0 ao nível alfa."""
    nome = resultado["teste"].replace("_", " ")
    situacao = "rejeita H0 (há diferença entre os grupos)"
    if resultado["p_valor"] >= alfa:
        situacao = "não rejeita H0 (sem evidência de diferença entre os grupos)"
    return f"{nome}: p-valor={resultado['p_valor']:.4f}, alfa={alfa} -> {situacao}."


def comparar_testes(rng) -> tuple[pd.DataFrame, list[str]]:
    """Gera um conjunto simulado, aplica os dois testes e salva o resultado em resultados/."""
    simulados = gerar_simulados_por_grupo(rng)
    welch = aplicar_welch(simulados["sem_bot"], simulados["com_bot"])
    mann_whitney = aplicar_mannwhitney(simulados["sem_bot"], simulados["com_bot"])

    tabela = pd.DataFrame([welch, mann_whitney])
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    tabela.to_csv(PASTA_RESULTADOS / "testes_exemplo.csv", index=False, float_format="%.4f")

    interpretacoes = [interpretar(welch), interpretar(mann_whitney)]
    return tabela, interpretacoes


def main() -> None:
    _, interpretacoes = comparar_testes(criar_rng())
    for linha in interpretacoes:
        print(linha)


if __name__ == "__main__":
    main()
