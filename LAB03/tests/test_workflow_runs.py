"""Testes da coleta de workflow runs. As respostas da API sao simuladas."""

from __future__ import annotations

from datetime import date

from pipeline.criterio_inclusao import Janela
from pipeline.workflow_runs import (
    coletar_runs_repositorio,
    coletar_workflow_runs,
    fatias_mensais,
)

JANELA = Janela("2024-01-01", "2024-03-31")


def run_api(id_: int, created_at: str, conclusion: str = "success") -> dict:
    return {
        "id": id_,
        "workflow_id": 1,
        "name": "CI",
        "conclusion": conclusion,
        "created_at": created_at,
        "run_started_at": created_at,
        "updated_at": created_at,
        "head_sha": "abc",  # campo que nao e guardado
    }


class FakeClient:
    """`runs` sao todos os runs do repositorio; as consultas filtram por `created`.

    `total_count` pode ser forcado por fatia em `totais` (ex.: para simular o teto).
    """

    def __init__(self, runs: list[dict], totais: dict[str, int] | None = None):
        self.runs = runs
        self.totais = totais or {}
        self.contagens: list[str] = []
        self.paginacoes: list[dict] = []

    def _na_fatia(self, created: str) -> list[dict]:
        inicio, fim = created.split("..")
        return [r for r in self.runs if inicio <= r["created_at"][:10] <= fim]

    def get(self, path, params=None):
        assert params["branch"] == "main" and params["event"] == "push"
        self.contagens.append(params["created"])
        total = self.totais.get(params["created"], len(self._na_fatia(params["created"])))
        return {"total_count": total}

    def get_paginated(self, path, params=None, items_key=None, max_pages=None):
        assert items_key == "workflow_runs" and max_pages == 10
        self.paginacoes.append(params)
        yield from self._na_fatia(params["created"])


def test_fatias_mensais_cobrem_a_janela_sem_buracos():
    assert fatias_mensais(Janela("2025-10-01", "2026-09-30"))[0] == (date(2025, 10, 1), date(2025, 10, 31))
    assert fatias_mensais(Janela("2025-10-01", "2026-09-30"))[-1] == (date(2026, 9, 1), date(2026, 9, 30))
    assert len(fatias_mensais(Janela("2025-10-01", "2026-09-30"))) == 12
    assert fatias_mensais(Janela("2024-02-10", "2024-03-05")) == [
        (date(2024, 2, 10), date(2024, 2, 29)),
        (date(2024, 3, 1), date(2024, 3, 5)),
    ]


def test_coleta_mes_a_mes_e_guarda_so_os_campos_usados():
    client = FakeClient(
        [run_api(2, "2024-02-10T00:00:00Z"), run_api(1, "2024-01-05T00:00:00Z", "failure")]
    )
    runs, no_teto = coletar_runs_repositorio(client, "org/a", "main", JANELA)

    assert client.contagens == ["2024-01-01..2024-01-31", "2024-02-01..2024-02-29", "2024-03-01..2024-03-31"]
    # Marco nao tem runs: nao pagina.
    assert [p["created"] for p in client.paginacoes] == ["2024-01-01..2024-01-31", "2024-02-01..2024-02-29"]
    assert [r["id"] for r in runs] == [1, 2]
    assert "head_sha" not in runs[0]
    assert runs[0]["conclusion"] == "failure"
    assert no_teto == 0


def test_mes_acima_do_teto_e_dividido_ao_meio():
    client = FakeClient(
        [run_api(1, "2024-01-05T00:00:00Z"), run_api(2, "2024-01-25T00:00:00Z")],
        totais={"2024-01-01..2024-01-31": 1500},
    )
    runs, no_teto = coletar_runs_repositorio(client, "org/a", "main", JANELA)

    assert client.contagens[:3] == [
        "2024-01-01..2024-01-31",
        "2024-01-01..2024-01-16",
        "2024-01-17..2024-01-31",
    ]
    assert [r["id"] for r in runs] == [1, 2]
    assert no_teto == 0


def test_dia_acima_do_teto_e_coletado_ate_o_limite_e_contado():
    client = FakeClient(
        [run_api(1, "2024-01-05T00:00:00Z")],
        totais={
            "2024-01-01..2024-01-31": 1500,
            "2024-01-01..2024-01-16": 1500,
            "2024-01-01..2024-01-08": 1500,
            "2024-01-05..2024-01-08": 1500,
            "2024-01-05..2024-01-06": 1500,
            "2024-01-05..2024-01-05": 1500,
        },
    )
    runs, no_teto = coletar_runs_repositorio(client, "org/a", "main", JANELA)

    assert [r["id"] for r in runs] == [1]
    assert no_teto == 1


def test_coletar_workflow_runs_usa_cache_e_refaz_cache_de_outra_janela(tmp_path):
    repos = [{"full_name": "org/a", "default_branch": "main"}]
    client = FakeClient([run_api(1, "2024-01-05T00:00:00Z")])
    coletar_workflow_runs(client, repos, JANELA, tmp_path)
    assert client.contagens

    client_2 = FakeClient([])
    resultado = coletar_workflow_runs(client_2, repos, JANELA, tmp_path)
    assert client_2.contagens == []
    assert resultado["org/a"]["runs"][0]["id"] == 1
    assert resultado["org/a"]["janela"] == "2024-01-01..2024-03-31"

    client_3 = FakeClient([])
    resultado = coletar_workflow_runs(client_3, repos, Janela("2024-01-01", "2024-01-31"), tmp_path)
    assert client_3.contagens == ["2024-01-01..2024-01-31"]
    assert resultado["org/a"]["runs"] == []


def test_coletar_workflow_runs_informa_progresso_e_mantem_a_ordem(tmp_path):
    repos = [
        {"full_name": "org/b", "default_branch": "main"},
        {"full_name": "org/a", "default_branch": "main"},
    ]
    chamadas = []
    resultado = coletar_workflow_runs(
        FakeClient([]), repos, JANELA, tmp_path, progresso=lambda f, t: chamadas.append((f, t))
    )
    assert chamadas == [(1, 2), (2, 2)]
    assert list(resultado) == ["org/b", "org/a"]
    assert (tmp_path / "workflow_runs" / "org__a.json").exists()
