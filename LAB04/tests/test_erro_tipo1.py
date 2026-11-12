from scipy import stats

from lab04.config import criar_rng
from lab04.erro_tipo1 import (
    calcular_erro_tipo1,
    construir_situacoes,
    grafico_erro_tipo1,
    simular_taxa_erro_tipo1,
)


def test_simular_taxa_erro_tipo1_fica_perto_de_5_por_cento():
    rng = criar_rng()
    taxas = simular_taxa_erro_tipo1(
        stats.norm, (0, 1), 30, rng, n_simulacoes=2000
    )
    assert 0.02 < taxas["welch"] < 0.08
    assert 0.02 < taxas["mann_whitney"] < 0.08


def test_construir_situacoes_cobre_as_tres_situacoes():
    situacoes = construir_situacoes()
    assert set(situacoes) == {
        "ajuste real (n=30)",
        "amostra pequena (n=10)",
        "cauda pesada (lognormal, forma=2.5)",
    }
    assert situacoes["amostra pequena (n=10)"]["n"] == 10


def test_calcular_erro_tipo1_retorna_uma_linha_por_situacao_e_teste():
    tabela = calcular_erro_tipo1(criar_rng())
    assert set(tabela["teste"]) == {"welch", "mann_whitney"}
    assert len(tabela) == len(construir_situacoes()) * 2
    assert tabela["taxa_erro_tipo1"].between(0, 1).all()


def test_grafico_erro_tipo1_tem_uma_serie_por_teste():
    tabela = calcular_erro_tipo1(criar_rng())
    figura = grafico_erro_tipo1(tabela)
    nomes_series = {trace.name for trace in figura.data}
    assert nomes_series == {"t de Welch", "Mann-Whitney"}
