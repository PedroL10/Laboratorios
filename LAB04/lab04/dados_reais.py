"""Aplica os dois testes aos dados reais e calcula o tamanho do efeito de cada um."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from lab04.config import ALFA
from lab04.distribuicao import carregar_grupos

RAIZ = Path(__file__).parent.parent
PASTA_RESULTADOS = RAIZ / "resultados"


def analisar_welch(sem_bot: np.ndarray, com_bot: np.ndarray) -> dict:
    """t de Welch com a diferença das médias (com bot − sem bot), seu IC 95% e o d de Cohen."""
    resultado = stats.ttest_ind(com_bot, sem_bot, equal_var=False)
    intervalo = resultado.confidence_interval(1 - ALFA)
    diferenca = com_bot.mean() - sem_bot.mean()
    desvio_combinado = np.sqrt((com_bot.var(ddof=1) + sem_bot.var(ddof=1)) / 2)
    return {
        "teste": "welch",
        "estatistica": resultado.statistic,
        "p_valor": resultado.pvalue,
        "efeito": "Diferença das médias (com bot − sem bot)",
        "valor_efeito": diferenca,
        "ic_inferior": intervalo.low,
        "ic_superior": intervalo.high,
        "efeito_padronizado": "d de Cohen",
        "valor_padronizado": diferenca / desvio_combinado,
    }


def analisar_mannwhitney(sem_bot: np.ndarray, com_bot: np.ndarray) -> dict:
    """Mann-Whitney com a chance de um PR com bot demorar mais e a correlação rank-biserial.

    U conta os pares (PR com bot, PR sem bot) em que o PR com bot demorou mais. Dividido pelo
    total de pares, é a probabilidade de superioridade; a correlação rank-biserial a reescala
    para ir de −1 a 1, com 0 quando não há diferença.
    """
    resultado = stats.mannwhitneyu(com_bot, sem_bot, alternative="two-sided")
    chance = resultado.statistic / (len(com_bot) * len(sem_bot))
    return {
        "teste": "mann_whitney",
        "estatistica": resultado.statistic,
        "p_valor": resultado.pvalue,
        "efeito": "Chance de um PR com bot demorar mais",
        "valor_efeito": chance,
        "ic_inferior": np.nan,
        "ic_superior": np.nan,
        "efeito_padronizado": "Correlação rank-biserial",
        "valor_padronizado": 2 * chance - 1,
    }


def classificar_efeito(teste: str, valor_padronizado: float) -> str:
    """Rótulo usual do tamanho do efeito, pelos limiares de Cohen para d e para correlações."""
    limites = (0.2, 0.5, 0.8) if teste == "welch" else (0.1, 0.3, 0.5)
    tamanho = abs(valor_padronizado)
    if tamanho < limites[0]:
        return "desprezível"
    if tamanho < limites[1]:
        return "pequeno"
    if tamanho < limites[2]:
        return "médio"
    return "grande"


def analisar_dados_reais() -> pd.DataFrame:
    """Aplica os dois testes aos dados reais, salva e retorna a tabela da seção 6."""
    grupos = carregar_grupos()
    sem_bot, com_bot = grupos["sem_bot"], grupos["com_bot"]
    tabela = pd.DataFrame(
        [analisar_welch(sem_bot, com_bot), analisar_mannwhitney(sem_bot, com_bot)]
    )
    tabela["rejeita_h0"] = tabela["p_valor"] < ALFA
    tabela["tamanho_efeito"] = [
        classificar_efeito(t, v) for t, v in zip(tabela["teste"], tabela["valor_padronizado"])
    ]
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    tabela.to_csv(PASTA_RESULTADOS / "dados_reais.csv", index=False, float_format="%.4f")
    return tabela
