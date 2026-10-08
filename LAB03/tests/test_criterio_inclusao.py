"""Testes do criterio de inclusao. Releases e workflow runs sao simulados."""

from __future__ import annotations

from datetime import date

import pytest
import requests

from pipeline.criterio_inclusao import (
    RELEASES_ANTIGAS_PARA_PARAR,
    Janela,
    aplicar_criterio,
    avaliar_repositorio,
    contar_releases_na_janela,
    contar_runs,
    incluido,
    parse_data,
)

JANELA = Janela("2025-10-01", "2026-09-30")
DENTRO = "2026-03-15T12:00:00Z"
ANTES = "2025-06-01T12:00:00Z"
DEPOIS = "2026-10-05T12:00:00Z"


def release(publicada=DENTRO, criada=None, draft=False, prerelease=False) -> dict:
    return {
        "created_at": criada or publicada or DENTRO,
        "published_at": publicada,
        "draft": draft,
        "prerelease": prerelease,
    }


def runs(**por_conclusao: int) -> list[dict]:
    """runs(success=40, failure=5) -> lista de runs com essas conclusoes."""
    return [{"conclusion": c} for c, n in por_conclusao.items() for _ in range(n)]


def http_error(status: int, headers: dict | None = None) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers or {})
    return requests.HTTPError(f"HTTP {status}", response=response)


class FakeClient:
    """Simula releases e workflow runs. Os runs informados ja sao do default
    branch, de push e dentro da janela (o filtro e da API real)."""

    def __init__(self, releases=None, workflow_runs=None, erros=None, teto=2500):
        self.teto = teto  # a API real satura o total_count dos runs em 2.500
        self.releases = releases or {}
        self.workflow_runs = workflow_runs or {}
        self.erros = erros or {}
        self.chamadas: list[tuple[str, dict | None]] = []
        self.releases_lidas = 0

    def _repo(self, path: str) -> str:
        return "/".join(path.split("/")[2:4])

    def _checar_erro(self, path: str) -> None:
        erro = self.erros.get(self._repo(path))
        if erro:
            raise erro

    def get(self, path, params=None):
        self.chamadas.append((path, params))
        self._checar_erro(path)
        lista = self.workflow_runs[self._repo(path)]
        if "status" in params:
            n = sum(r["conclusion"] == params["status"] for r in lista)
        else:
            n = len(lista)
        return {"total_count": min(n, self.teto)}

    def get_paginated(self, path, params=None, items_key=None, max_pages=None):
        self.chamadas.append((path, params))
        self._checar_erro(path)
        if path.endswith("/releases"):
            for r in self.releases[self._repo(path)]:
                self.releases_lidas += 1
                yield r
        else:
            assert items_key == "workflow_runs"
            yield from self.workflow_runs[self._repo(path)]


def repo(nome: str) -> dict:
    return {"full_name": f"org/{nome}", "default_branch": "main"}


# --- Janela ---------------------------------------------------------------

def test_janela_inclui_o_primeiro_e_o_ultimo_dia():
    assert JANELA.contem(parse_data("2025-10-01T00:00:00Z"))
    assert JANELA.contem(parse_data("2026-09-30T23:59:59Z"))
    assert not JANELA.contem(parse_data("2025-09-30T23:59:59Z"))
    assert not JANELA.contem(parse_data("2026-10-01T00:00:00Z"))


def test_janela_aceita_date_e_monta_filtro_created():
    janela = Janela(date(2025, 10, 1), date(2026, 9, 30))
    assert janela.filtro_created() == "2025-10-01..2026-09-30"


def test_janela_invertida_e_rejeitada():
    with pytest.raises(ValueError):
        Janela("2026-09-30", "2025-10-01")


# --- Releases -------------------------------------------------------------

def test_conta_apenas_releases_publicadas_dentro_da_janela():
    client = FakeClient(
        releases={
            "org/a": [
                release(DEPOIS),               # depois da janela
                release(DENTRO),               # conta
                release(DENTRO),               # conta
                release(DENTRO, draft=True),   # draft
                release(DENTRO, prerelease=True),  # pre-release
                release(None, criada=DENTRO),  # sem published_at
                release(ANTES),                # antes da janela
            ]
        }
    )
    assert contar_releases_na_janela(client, "org/a", JANELA) == 2


def test_para_de_paginar_apos_muitas_releases_antigas_seguidas():
    lista = [release(DENTRO)] * 5 + [release(ANTES)] * 1000
    client = FakeClient(releases={"org/a": lista})

    assert contar_releases_na_janela(client, "org/a", JANELA) == 5
    assert client.releases_lidas == 5 + RELEASES_ANTIGAS_PARA_PARAR


def test_release_antiga_fora_de_ordem_nao_interrompe_a_contagem():
    lista = [release(DENTRO)] + [release(ANTES)] * 50 + [release(DENTRO)]
    client = FakeClient(releases={"org/a": lista})
    assert contar_releases_na_janela(client, "org/a", JANELA) == 2


# --- Workflow runs --------------------------------------------------------

def test_poucos_runs_de_push_nao_conta_validos():
    client = FakeClient(workflow_runs={"org/a": runs(success=30)})

    assert contar_runs(client, "org/a", "main", JANELA, 50) == (30, None)
    assert len(client.chamadas) == 1


def test_runs_validos_somam_sucessos_e_falhas_e_ignoram_cancelados():
    client = FakeClient(
        workflow_runs={"org/a": runs(success=40, failure=8, timed_out=2, cancelled=30, skipped=5)}
    )
    assert contar_runs(client, "org/a", "main", JANELA, 50) == (85, 50)


def test_consulta_de_runs_usa_branch_push_e_janela():
    client = FakeClient(workflow_runs={"org/a": runs(success=60)})
    contar_runs(client, "org/a", "develop", JANELA, 50)

    path, params = client.chamadas[0]
    assert path == "/repos/org/a/actions/runs"
    assert params["branch"] == "develop"
    assert params["event"] == "push"
    assert params["created"] == "2025-10-01..2026-09-30"


def test_startup_failure_e_contado_listando_os_runs():
    # 45 + 0 + 0 pelo filtro de status ficaria abaixo de 50, mas ha 10 startup_failure.
    client = FakeClient(
        workflow_runs={"org/a": runs(success=45, startup_failure=10, cancelled=5)}
    )
    assert contar_runs(client, "org/a", "main", JANELA, 50) == (60, 55)


# --- Avaliacao de um repositorio -----------------------------------------

def test_repositorio_que_atende_o_criterio_e_incluido():
    client = FakeClient(
        releases={"org/a": [release(DENTRO)] * 6},
        workflow_runs={"org/a": runs(success=50, failure=10)},
    )
    linha = avaliar_repositorio(client, repo("a"), JANELA, 5, 50)

    assert linha["incluido"] is True
    assert linha["n_releases_janela"] == 6
    assert (linha["n_runs_push"], linha["n_runs_validos"]) == (60, 60)
    assert linha["runs_no_teto"] is False
    assert linha["motivo_descarte"] == ""


def test_contagem_no_teto_da_api_e_sinalizada():
    # Cada contagem satura em 2.500 separadamente: a soma dos validos passa do total.
    client = FakeClient(
        releases={"org/a": [release(DENTRO)] * 5},
        workflow_runs={"org/a": runs(success=2600, failure=100)},
    )
    linha = avaliar_repositorio(client, repo("a"), JANELA, 5, 50)

    assert linha["incluido"] is True
    assert (linha["n_runs_push"], linha["n_runs_validos"]) == (2500, 2600)
    assert linha["runs_no_teto"] is True


def test_poucas_releases_descarta_sem_consultar_runs():
    client = FakeClient(releases={"org/a": [release(DENTRO)] * 4})
    linha = avaliar_repositorio(client, repo("a"), JANELA, 5, 50)

    assert linha["incluido"] is False
    assert linha["motivo_descarte"] == "menos_de_5_releases"
    assert all(path.endswith("/releases") for path, _ in client.chamadas)


def test_poucos_runs_validos_descarta():
    client = FakeClient(
        releases={"org/a": [release(DENTRO)] * 5},
        workflow_runs={"org/a": runs(success=20, cancelled=100)},
    )
    linha = avaliar_repositorio(client, repo("a"), JANELA, 5, 50)

    assert linha["incluido"] is False
    assert linha["motivo_descarte"] == "menos_de_50_runs_validos"
    assert linha["n_runs_validos"] == 20


def test_erro_http_vira_motivo_de_descarte():
    client = FakeClient(erros={"org/a": http_error(404)})
    linha = avaliar_repositorio(client, repo("a"), JANELA, 5, 50)
    assert linha["motivo_descarte"] == "erro_http_404"


def test_cota_esgotada_interrompe():
    client = FakeClient(erros={"org/a": http_error(403, {"X-RateLimit-Remaining": "0"})})
    with pytest.raises(requests.HTTPError):
        avaliar_repositorio(client, repo("a"), JANELA, 5, 50)


# --- Aplicacao na lista de candidatos ------------------------------------

def client_com(bons: list[str], ruins: list[str]) -> FakeClient:
    releases = {f"org/{n}": [release(DENTRO)] * 5 for n in bons}
    releases.update({f"org/{n}": [] for n in ruins})
    workflow_runs = {f"org/{n}": runs(success=50) for n in bons}
    return FakeClient(releases=releases, workflow_runs=workflow_runs)


def test_para_ao_atingir_n_repos(tmp_path):
    client = client_com(["a", "c", "d"], ["b"])
    avaliados = aplicar_criterio(
        client, [repo(n) for n in "abcd"], JANELA, 5, 50, 2, tmp_path / "c.csv"
    )

    assert [a["full_name"] for a in avaliados] == ["org/a", "org/b", "org/c"]
    assert [incluido(a) for a in avaliados] == [True, False, True]
    # org/d nao chegou a ser consultado
    assert not any("org/d" in path for path, _ in client.chamadas)


def test_sem_n_repos_avalia_todos(tmp_path):
    client = client_com(["a", "c", "d"], ["b"])
    avaliados = aplicar_criterio(
        client, [repo(n) for n in "abcd"], JANELA, 5, 50, None, tmp_path / "c.csv"
    )
    assert sum(incluido(a) for a in avaliados) == 3


def test_retomada_continua_sem_reavaliar(tmp_path):
    saida = tmp_path / "c.csv"
    aplicar_criterio(client_com(["a"], ["b"]), [repo("a"), repo("b")], JANELA, 5, 50, None, saida)

    client = client_com(["a", "c"], ["b"])
    avaliados = aplicar_criterio(
        client, [repo(n) for n in "abc"], JANELA, 5, 50, None, saida
    )

    assert {path.split("/")[3] for path, _ in client.chamadas} == {"c"}
    assert [incluido(a) for a in avaliados] == [True, False, True]


def test_retomada_com_n_repos_menor_corta_a_amostra(tmp_path):
    saida = tmp_path / "c.csv"
    lista = [repo(n) for n in "abc"]
    aplicar_criterio(client_com(["a", "b", "c"], []), lista, JANELA, 5, 50, None, saida)

    client = client_com(["a", "b", "c"], [])
    avaliados = aplicar_criterio(client, lista, JANELA, 5, 50, 2, saida)

    assert [a["full_name"] for a in avaliados] == ["org/a", "org/b"]
    assert client.chamadas == []


def test_progresso_e_informado(tmp_path):
    chamadas = []
    aplicar_criterio(
        client_com(["a"], ["b"]),
        [repo("a"), repo("b")],
        JANELA, 5, 50, None, tmp_path / "c.csv",
        progresso=lambda feitos, total: chamadas.append((feitos, total)),
    )
    assert chamadas == [(1, 2), (2, 2)]


def test_erro_5xx_interrompe_em_vez_de_descartar():
    client = FakeClient(erros={"org/a": http_error(504)})
    with pytest.raises(requests.HTTPError):
        avaliar_repositorio(client, repo("a"), JANELA, 5, 50)


def test_retomada_reavalia_repositorio_que_ficou_para_tras(tmp_path):
    # 1a execucao: org/b deu erro temporario no meio; org/a e org/c foram incluidos.
    saida = tmp_path / "c.csv"
    lista = [repo(n) for n in "abc"]
    client = client_com(["a", "b", "c"], [])
    client.erros = {"org/b": http_error(504)}
    with pytest.raises(requests.HTTPError):
        aplicar_criterio(client, lista, JANELA, 5, 50, 2, saida)
    aplicar_criterio(client_com(["a", "c"], []), [lista[0], lista[2]], JANELA, 5, 50, 2, saida)

    # 2a execucao com a lista completa: org/b vem antes de org/c e precisa ser avaliado,
    # mesmo com a amostra ja tendo 2 incluidos no arquivo.
    client = client_com(["a", "b", "c"], [])
    avaliados = aplicar_criterio(client, lista, JANELA, 5, 50, 2, saida)

    assert {path.split("/")[3] for path, _ in client.chamadas} == {"b"}
    assert [a["full_name"] for a in avaliados] == ["org/a", "org/b"]
