"""Testes do cliente HTTP. Nenhum teste acessa a API real: as respostas sao simuladas."""

from __future__ import annotations

import pytest
import requests

from pipeline.github_client import GitHubClient, MissingTokenError, read_token


class FakeResponse:
    def __init__(
        self,
        payload,
        next_url: str | None = None,
        status_code: int = 200,
        headers: dict | None = None,
    ):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}
        self.links = {"next": {"url": next_url}} if next_url else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Devolve as respostas na ordem e registra cada chamada feita."""

    def __init__(self, responses: list[FakeResponse]):
        self.headers: dict = {}
        self.responses = list(responses)
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        resposta = self.responses.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def make_client(responses: list[FakeResponse]) -> tuple[GitHubClient, FakeSession]:
    session = FakeSession(responses)
    return GitHubClient(token="token-de-teste", session=session), session


def test_read_token_le_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "abc123")
    assert read_token() == "abc123"


def test_read_token_sem_variavel_levanta_erro(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(MissingTokenError):
        read_token()


def test_cliente_envia_token_no_cabecalho():
    client, session = make_client([])
    assert session.headers["Authorization"] == "Bearer token-de-teste"
    assert session.headers["Accept"] == "application/vnd.github+json"


def test_get_monta_url_a_partir_do_caminho():
    client, session = make_client([FakeResponse({"ok": True})])
    assert client.get("/rate_limit") == {"ok": True}
    assert session.calls[0][0] == "https://api.github.com/rate_limit"


def test_get_paginated_segue_link_next_ate_o_fim():
    client, session = make_client(
        [
            FakeResponse([{"id": 1}, {"id": 2}], next_url="https://api.github.com/x?page=2"),
            FakeResponse([{"id": 3}]),
        ]
    )
    itens = list(client.get_paginated("/x"))

    assert [i["id"] for i in itens] == [1, 2, 3]
    assert session.calls[0] == ("https://api.github.com/x", {"per_page": 100})
    # A segunda pagina usa a URL do Link, que ja traz os parametros.
    assert session.calls[1] == ("https://api.github.com/x?page=2", None)


def test_get_paginated_com_items_key_le_lista_dentro_do_objeto():
    client, _ = make_client(
        [FakeResponse({"total_count": 2, "workflow_runs": [{"id": 10}, {"id": 11}]})]
    )
    itens = list(client.get_paginated("/runs", items_key="workflow_runs"))
    assert [i["id"] for i in itens] == [10, 11]


def test_get_paginated_respeita_max_pages():
    client, session = make_client(
        [
            FakeResponse([{"id": 1}], next_url="https://api.github.com/x?page=2"),
            FakeResponse([{"id": 2}]),
        ]
    )
    assert [i["id"] for i in client.get_paginated("/x", max_pages=1)] == [1]
    assert len(session.calls) == 1


def test_erro_http_e_propagado():
    client, _ = make_client([FakeResponse({}, status_code=404)])
    with pytest.raises(requests.HTTPError):
        client.get("/repos/nao/existe")


# --- Rate limit e erros temporarios ----------------------------------------

AGORA = 1_800_000_000.0


class Relogio:
    """Registra as esperas sem dormir de verdade."""

    def __init__(self):
        self.esperas: list[float] = []
        self.avisos: list[str] = []

    def sleep(self, segundos):
        self.esperas.append(segundos)


def cliente_com_relogio(responses) -> tuple[GitHubClient, FakeSession, Relogio]:
    session = FakeSession(responses)
    relogio = Relogio()
    client = GitHubClient(
        token="t",
        session=session,
        sleep=relogio.sleep,
        agora=lambda: AGORA,
        aviso=relogio.avisos.append,
    )
    return client, session, relogio


def cota_esgotada_resp(reset: float = AGORA + 60, status: int = 403) -> FakeResponse:
    return FakeResponse(
        {"message": "API rate limit exceeded"},
        status_code=status,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(reset))},
    )


def test_cota_esgotada_espera_ate_o_reset_e_repete():
    client, session, relogio = cliente_com_relogio([cota_esgotada_resp(), FakeResponse({"ok": 1})])

    assert client.get("/x") == {"ok": 1}
    assert relogio.esperas == [65.0]  # 60 s ate o reset + 5 s de margem
    assert len(session.calls) == 2
    assert "Limite da API atingido" in relogio.avisos[0]


def test_cota_esgotada_com_429_tambem_espera():
    client, _, relogio = cliente_com_relogio([cota_esgotada_resp(status=429), FakeResponse({})])
    client.get("/x")
    assert relogio.esperas == [65.0]


def test_reset_no_passado_espera_so_a_margem():
    client, _, relogio = cliente_com_relogio([cota_esgotada_resp(reset=AGORA - 10), FakeResponse({})])
    client.get("/x")
    assert relogio.esperas == [5.0]


def test_limite_secundario_respeita_retry_after():
    limite = FakeResponse({}, status_code=429, headers={"Retry-After": "30"})
    client, _, relogio = cliente_com_relogio([limite, FakeResponse({"ok": 1})])

    assert client.get("/x") == {"ok": 1}
    assert relogio.esperas == [30.0]


def test_cota_que_nunca_renova_desiste_apos_o_limite_de_esperas():
    from pipeline.github_client import MAX_ESPERAS_COTA

    client, session, relogio = cliente_com_relogio(
        [cota_esgotada_resp() for _ in range(MAX_ESPERAS_COTA + 1)]
    )
    with pytest.raises(requests.HTTPError):
        client.get("/x")
    assert len(relogio.esperas) == MAX_ESPERAS_COTA
    assert len(session.calls) == MAX_ESPERAS_COTA + 1


def test_403_que_nao_e_limite_nao_espera():
    # ex.: "contributor list is too large" — erro definitivo, tratado por quem chamou
    grande = FakeResponse({"message": "too large"}, status_code=403, headers={"X-RateLimit-Remaining": "4000"})
    client, session, relogio = cliente_com_relogio([grande])

    with pytest.raises(requests.HTTPError):
        client.get("/x")
    assert relogio.esperas == []
    assert len(session.calls) == 1


def test_erro_5xx_repete_com_backoff_e_recupera():
    client, session, relogio = cliente_com_relogio(
        [FakeResponse({}, status_code=502), FakeResponse({}, status_code=504), FakeResponse({"ok": 1})]
    )
    assert client.get("/x") == {"ok": 1}
    assert relogio.esperas == [1.0, 2.0]
    assert "Erro temporario do GitHub (502)" in relogio.avisos[0]


def test_erro_5xx_persistente_desiste_apos_max_tentativas():
    client, session, relogio = cliente_com_relogio([FakeResponse({}, status_code=500) for _ in range(6)])

    with pytest.raises(requests.HTTPError):
        client.get("/x")
    assert relogio.esperas == [1.0, 2.0, 4.0, 8.0, 16.0]
    assert len(session.calls) == 6


def test_falha_de_rede_repete_com_backoff():
    client, _, relogio = cliente_com_relogio(
        [requests.ConnectionError("queda"), requests.Timeout("lento"), FakeResponse({"ok": 1})]
    )
    assert client.get("/x") == {"ok": 1}
    assert relogio.esperas == [1.0, 2.0]
    assert "Falha de rede (ConnectionError)" in relogio.avisos[0]


def test_conexao_interrompida_no_meio_da_resposta_repete_com_backoff():
    client, _, relogio = cliente_com_relogio(
        [requests.exceptions.ChunkedEncodingError("IncompleteRead"), FakeResponse({"ok": 1})]
    )
    assert client.get("/x") == {"ok": 1}
    assert relogio.esperas == [1.0]
    assert "Falha de rede (ChunkedEncodingError)" in relogio.avisos[0]


def test_falha_de_rede_persistente_propaga_o_erro():
    client, _, relogio = cliente_com_relogio([requests.ConnectionError("queda") for _ in range(6)])
    with pytest.raises(requests.ConnectionError):
        client.get("/x")
    assert len(relogio.esperas) == 5


def test_erro_4xx_comum_nao_e_repetido():
    client, session, relogio = cliente_com_relogio([FakeResponse({}, status_code=404)])
    with pytest.raises(requests.HTTPError):
        client.get("/x")
    assert relogio.esperas == []
    assert len(session.calls) == 1


def test_paginacao_continua_depois_de_esperar_a_cota():
    client, session, relogio = cliente_com_relogio(
        [
            FakeResponse([{"id": 1}], next_url="https://api.github.com/x?page=2"),
            cota_esgotada_resp(),
            FakeResponse([{"id": 2}]),
        ]
    )
    assert [i["id"] for i in client.get_paginated("/x")] == [1, 2]
    assert relogio.esperas == [65.0]
    # a pagina 2 foi pedida de novo com a mesma URL
    assert session.calls[1] == session.calls[2] == ("https://api.github.com/x?page=2", None)
