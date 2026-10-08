"""Testes das funcoes de lead time. Os exemplos vem do enunciado (secao 5, RQ 02)."""

from __future__ import annotations

from metricas.lead_time import (
    lead_time_dias,
    lead_time_por_release,
    lead_time_repositorio,
    lead_times_por_commit,
    mediana,
)


def release(published_at: str, *commits: str) -> dict:
    return {"tag_name": "v", "published_at": published_at, "commits": list(commits)}


def test_lead_time_dias_calcula_diferenca_em_dias():
    assert lead_time_dias(
        datetime_iso("2024-03-15T00:00:00Z"), datetime_iso("2024-03-02T00:00:00Z")
    ) == 13


def datetime_iso(valor: str):
    from datetime import datetime

    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def test_exemplo_do_enunciado_variante_a():
    # v1.1 publicada 15/03, commits de 02/03, 10/03 e 14/03 -> lead time 13 dias.
    r = release("2024-03-15T00:00:00Z", "2024-03-02T00:00:00Z", "2024-03-10T00:00:00Z", "2024-03-14T00:00:00Z")
    assert lead_time_por_release(r) == 13


def test_exemplo_do_enunciado_variante_b():
    r = release("2024-03-15T00:00:00Z", "2024-03-02T00:00:00Z", "2024-03-10T00:00:00Z", "2024-03-14T00:00:00Z")
    assert lead_times_por_commit(r) == [13, 5, 1]


def test_release_sem_commits_novos_nao_entra_na_variante_a():
    r = release("2024-03-15T00:00:00Z")
    assert lead_time_por_release(r) is None
    assert lead_times_por_commit(r) == []


def test_mediana_de_lista_vazia_e_none():
    assert mediana([]) is None


def test_mediana_de_lista_com_valores():
    assert mediana([1, 2, 3]) == 2


def test_lead_time_repositorio_agrega_variantes_e_ignora_releases_sem_commits():
    releases = [
        release("2024-03-15T00:00:00Z", "2024-03-02T00:00:00Z", "2024-03-14T00:00:00Z"),
        release("2024-04-01T00:00:00Z"),  # republicada sem mudancas: sem commits
        release("2024-04-10T00:00:00Z", "2024-04-09T00:00:00Z"),
    ]

    resultado = lead_time_repositorio(releases)

    # variante (a): [13, 1] (a 2a release fica de fora por nao ter commits)
    assert resultado["lead_time_release_dias"] == 7
    assert resultado["n_releases_variante_a"] == 2
    # variante (b): todos os commits de todas as releases, [13, 1, 1]
    assert resultado["lead_time_commit_dias"] == 1
    assert resultado["n_commits_variante_b"] == 3


def test_lead_time_repositorio_sem_releases_devolve_none():
    resultado = lead_time_repositorio([])
    assert resultado == {
        "lead_time_release_dias": None,
        "lead_time_commit_dias": None,
        "n_releases_variante_a": 0,
        "n_commits_variante_b": 0,
    }
