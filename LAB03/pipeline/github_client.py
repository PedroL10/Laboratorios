"""Cliente HTTP proprio para a API REST do GitHub.

O enunciado proibe bibliotecas prontas de acesso a API do GitHub (ex.: PyGithub),
entao as chamadas sao feitas diretamente com `requests`.

Responsabilidades deste modulo:
- autenticar cada requisicao com o token lido da variavel de ambiente GITHUB_TOKEN;
- seguir a paginacao pelo cabecalho `Link` (rel="next") ate a ultima pagina.

O tratamento de rate limit, backoff e cache/retomada fica nas tasks proprias
e deve ser plugado em `GitHubClient._request`.
"""

from __future__ import annotations

import os
from typing import Iterator

import requests

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
TOKEN_ENV_VAR = "GITHUB_TOKEN"
DEFAULT_PER_PAGE = 100
DEFAULT_TIMEOUT_SECONDS = 30


class MissingTokenError(RuntimeError):
    """Levantado quando a variavel de ambiente GITHUB_TOKEN nao esta definida."""


def read_token() -> str:
    """Le o token do GitHub da variavel de ambiente. Nunca o token e commitado."""
    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if not token:
        raise MissingTokenError(
            f"Defina a variavel de ambiente {TOKEN_ENV_VAR} com um token do GitHub."
        )
    return token


def cota_esgotada(exc: requests.HTTPError) -> bool:
    """Diz se o erro HTTP e de cota esgotada (403/429 com X-RateLimit-Remaining = 0).

    Nesse caso a coleta deve parar para ser retomada depois, e nao descartar o repositorio.
    """
    response = exc.response
    if response is None or response.status_code not in (403, 429):
        return False
    return response.headers.get("X-RateLimit-Remaining") == "0"


def status_http(exc: requests.HTTPError) -> int | None:
    return exc.response.status_code if exc.response is not None else None


def erro_transitorio(exc: requests.HTTPError) -> bool:
    """Diz se o erro e passageiro (cota esgotada ou 5xx do servidor).

    Esses erros nao dizem nada sobre o repositorio: a coleta deve parar (ou repetir)
    em vez de descarta-lo.
    """
    status = status_http(exc)
    return cota_esgotada(exc) or (status is not None and status >= 500)


class GitHubClient:
    """Cliente minimo da API REST do GitHub, com autenticacao e paginacao."""

    def __init__(
        self,
        token: str | None = None,
        session: requests.Session | None = None,
        base_url: str = API_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token or read_token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
            }
        )

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            return path_or_url
        return f"{self.base_url}/{path_or_url.lstrip('/')}"

    def _request(self, url: str, params: dict | None = None) -> requests.Response:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    def get(self, path: str, params: dict | None = None) -> dict | list:
        """Faz um GET e devolve o JSON da resposta (uma unica pagina)."""
        return self._request(self._url(path), params).json()

    def get_paginated(
        self,
        path: str,
        params: dict | None = None,
        items_key: str | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict]:
        """Percorre todas as paginas de um endpoint e devolve os itens um a um.

        `items_key` indica onde estao os itens quando a resposta e um objeto,
        por exemplo "items" (search), "workflow_runs" (actions/runs) ou
        "workflows" (actions/workflows). Se for None, a resposta deve ser uma lista.
        """
        params = {"per_page": DEFAULT_PER_PAGE, **(params or {})}
        url: str | None = self._url(path)
        pages = 0
        while url:
            response = self._request(url, params)
            payload = response.json()
            items = payload[items_key] if items_key else payload
            yield from items

            pages += 1
            if max_pages is not None and pages >= max_pages:
                break
            # A URL de "next" ja traz todos os parametros da consulta.
            url = response.links.get("next", {}).get("url")
            params = None
