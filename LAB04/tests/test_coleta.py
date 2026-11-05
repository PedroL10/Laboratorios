import pytest

from lab04.coleta import TAMANHO_AMOSTRA, horas_ate_merge, montar_linhas, sortear
from lab04.config import criar_rng


def pr_da_api(numero=1, tipo="User", merge_em="2026-03-02T00:00:00Z"):
    return {
        "number": numero,
        "user": {"login": "autor", "type": tipo},
        "created_at": "2026-03-01T00:00:00Z",
        "pull_request": {"merged_at": merge_em},
    }


def test_horas_ate_merge():
    assert horas_ate_merge("2026-03-01T00:00:00Z", "2026-03-02T12:00:00Z") == 36


def test_montar_linhas_mantem_pr_de_humano_no_limite():
    linhas = montar_linhas([pr_da_api(merge_em="2026-03-31T00:00:00Z")], "sem_bot", "nenhuma")
    assert linhas[0]["horas_ate_merge"] == 720
    assert linhas[0]["grupo"] == "sem_bot"


def test_montar_linhas_descarta_autor_bot():
    assert montar_linhas([pr_da_api(tipo="Bot")], "sem_bot", "nenhuma") == []


def test_montar_linhas_descarta_pr_acima_do_limite():
    assert montar_linhas([pr_da_api(merge_em="2026-03-31T00:00:01Z")], "sem_bot", "nenhuma") == []


def test_sortear_nao_depende_da_ordem_da_api():
    linhas = montar_linhas([pr_da_api(n) for n in range(100)], "sem_bot", "nenhuma")
    amostra = sortear(linhas, criar_rng())
    invertida = sortear(linhas[::-1], criar_rng())
    assert len(amostra) == TAMANHO_AMOSTRA
    assert amostra["pr"].is_unique
    assert amostra["pr"].tolist() == invertida["pr"].tolist()


def test_sortear_falha_com_menos_elegiveis_que_a_amostra():
    with pytest.raises(ValueError):
        sortear(montar_linhas([pr_da_api()], "sem_bot", "nenhuma"), criar_rng())
