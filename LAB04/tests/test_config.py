from lab04.config import ALFA, N_SIMULACOES, SEMENTE, criar_rng


def test_parametros_seguem_o_enunciado():
    assert SEMENTE == 42
    assert ALFA == 0.05
    assert N_SIMULACOES == 10_000


def test_geradores_novos_produzem_a_mesma_sequencia():
    assert criar_rng().random(5).tolist() == criar_rng().random(5).tolist()
