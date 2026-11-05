import numpy as np
import pytest
from scipy import stats

from lab04.config import criar_rng
from lab04.distribuicao import carregar_grupos, comparar_ajustes, contar_outliers, resumir


def test_contar_outliers_acha_valor_extremo():
    assert contar_outliers(np.array([1.0, 2, 3, 4, 5, 100])) == 1


def test_contar_outliers_ignora_dados_sem_extremos():
    assert contar_outliers(np.arange(1.0, 11)) == 0


def test_resumir_calcula_medidas_nas_duas_escalas():
    horas = np.array([1.0, np.e, np.e**2])
    resumo = resumir(horas)
    assert resumo["n"] == 3
    assert resumo["mediana_h"] == pytest.approx(np.e)
    assert resumo["media_log"] == pytest.approx(1)
    assert resumo["dp_log"] == pytest.approx(1)


def test_comparar_ajustes_prefere_a_distribuicao_que_gerou_os_dados():
    horas = stats.lognorm.rvs(1.5, scale=20, size=2000, random_state=criar_rng())
    ajustes = comparar_ajustes(horas)
    assert ajustes.loc[0, "distribuicao"] == "lognormal"
    assert ajustes.loc[0, "delta_aic"] == 0
    assert ajustes.loc[0, "forma"] == pytest.approx(1.5, abs=0.1)
    assert ajustes.loc[0, "escala"] == pytest.approx(20, rel=0.1)


def test_comparar_ajustes_conta_gamma_sem_a_locacao_fixa():
    horas = stats.gamma.rvs(2, scale=10, size=2000, random_state=criar_rng())
    ajustes = comparar_ajustes(horas).set_index("distribuicao")
    log_verossimilhanca = stats.gamma.logpdf(
        horas, ajustes.loc["gamma", "forma"], 0, ajustes.loc["gamma", "escala"]
    ).sum()
    assert ajustes.loc["gamma", "aic"] == pytest.approx(2 * 2 - 2 * log_verossimilhanca)


def test_carregar_grupos_le_a_amostra_real():
    grupos = carregar_grupos()
    assert len(grupos["sem_bot"]) == 30
    assert len(grupos["com_bot"]) == 30
    assert len(grupos["todos"]) == 60
