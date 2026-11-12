import numpy as np

from lab04.config import criar_rng
from lab04.erro_tipo1 import construir_situacoes, extrair_erro_tipo1
from lab04.poder import FATORES_EFEITO, calcular_poder, grafico_poder


def test_fatores_comecam_sem_efeito_e_tem_pelo_menos_cinco_valores():
    assert FATORES_EFEITO[0] == 1.0
    assert len(FATORES_EFEITO) >= 5
    assert list(FATORES_EFEITO) == sorted(FATORES_EFEITO)


def test_calcular_poder_tem_uma_linha_por_situacao_fator_e_teste():
    tabela = calcular_poder(criar_rng(), fatores=(1.0, 2.0), n_simulacoes=500)
    assert len(tabela) == len(construir_situacoes()) * 2 * 2
    assert tabela["taxa_rejeicao"].between(0, 1).all()


def test_poder_cresce_com_o_efeito_na_situacao_real():
    tabela = calcular_poder(criar_rng(), fatores=(1.0, 2.5), n_simulacoes=2000)
    real = tabela[tabela["situacao"] == "ajuste real (n=30)"]
    for teste in ("welch", "mann_whitney"):
        taxas = real[real["teste"] == teste].sort_values("fator_efeito")["taxa_rejeicao"]
        assert np.all(np.diff(taxas) > 0)


def test_extrair_erro_tipo1_usa_so_o_fator_1():
    tabela = calcular_poder(criar_rng(), fatores=(1.0, 2.0), n_simulacoes=500)
    erro = extrair_erro_tipo1(tabela)
    assert len(erro) == len(construir_situacoes()) * 2
    sem_efeito = tabela[tabela["fator_efeito"] == 1.0]["taxa_rejeicao"].tolist()
    assert erro["taxa_erro_tipo1"].tolist() == sem_efeito


def test_grafico_poder_tem_uma_curva_por_teste_e_situacao():
    tabela = calcular_poder(criar_rng(), fatores=(1.0, 2.0), n_simulacoes=200)
    figura = grafico_poder(tabela)
    assert len(figura.data) == len(construir_situacoes()) * 2
