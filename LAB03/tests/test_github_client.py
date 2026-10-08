"""Testes do cliente HTTP. Nenhum teste acessa a API real: as respostas sao simuladas."""

from __future__ import annotations

import pytest
import requests

from pipeline.github_client import GitHubClient, MissingTokenError, read_token


class FakeResponse:
    def __init__(self, payload, next_url: str | None = None, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
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
        return self.responses.pop(0)


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
