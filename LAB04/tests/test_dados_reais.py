import numpy as np
import pytest

from lab04.dados_reais import (
    analisar_dados_reais,
    analisar_mannwhitney,
    analisar_welch,
    classificar_efeito,
)


def test_analisar_welch_mede_a_diferenca_das_medias_com_ic():
    sem_bot, com_bot = np.array([1.0, 2, 3, 4]), np.array([11.0, 12, 13, 14])
    resultado = analisar_welch(sem_bot, com_bot)
    assert resultado["valor_efeito"] == pytest.approx(10)
    assert resultado["ic_inferior"] < 10 < resultado["ic_superior"]
    assert resultado["valor_padronizado"] > 0


def test_analisar_mannwhitney_mede_a_chance_de_demorar_mais():
    sem_bot, com_bot = np.array([1.0, 2, 3, 4]), np.array([11.0, 12, 13, 14])
    resultado = analisar_mannwhitney(sem_bot, com_bot)
    assert resultado["valor_efeito"] == pytest.approx(1)
    assert resultado["valor_padronizado"] == pytest.approx(1)


@pytest.mark.parametrize(
    ("teste", "valor", "esperado"),
    [
        ("welch", 0.1, "desprezível"),
        ("welch", 0.53, "médio"),
        ("welch", -0.9, "grande"),
        ("mann_whitney", 0.27, "pequeno"),
        ("mann_whitney", 0.35, "médio"),
    ],
)
def test_classificar_efeito(teste, valor, esperado):
    assert classificar_efeito(teste, valor) == esperado


def test_analisar_dados_reais_tem_uma_linha_por_teste():
    tabela = analisar_dados_reais()
    assert list(tabela["teste"]) == ["welch", "mann_whitney"]
    assert tabela["p_valor"].between(0, 1).all()
