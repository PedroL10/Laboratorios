"""Cliente HTTP proprio para a API REST do GitHub.

O enunciado proibe bibliotecas prontas de acesso a API do GitHub (ex.: PyGithub),
entao as chamadas sao feitas diretamente com `requests`. Quase tudo usa a API REST;
a API GraphQL (`graphql`) so e usada onde a REST nao basta (ex.: listar tags
ordenadas pela data do commit, em `pipeline.tags`).

Responsabilidades deste modulo:
- autenticar cada requisicao com o token lido da variavel de ambiente GITHUB_TOKEN;
- seguir a paginacao pelo cabecalho `Link` (rel="next") ate a ultima pagina;
- tratar rate limit e erros temporarios (secao 7 do enunciado), em `_request`:
  - cota esgotada (403/429 com `X-RateLimit-Remaining: 0`): espera ate o horario
    de `X-RateLimit-Reset` e repete a chamada;
  - limite secundario (403/429 com `Retry-After`): espera os segundos indicados;
  - respostas 5xx e falhas de rede: repete com backoff exponencial
    (1 s, 2 s, 4 s, 8 s, 16 s) ate `max_tentativas`.
  Esgotadas as tentativas, o erro e propagado e a coleta pode ser retomada depois.

A retomada (nao repetir chamadas ja feitas) fica em `pipeline.retomada` e nos
caches de cada etapa.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from typing import Callable, Iterator

import requests

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"
TOKEN_ENV_VAR = "GITHUB_TOKEN"
DEFAULT_PER_PAGE = 100
DEFAULT_TIMEOUT_SECONDS = 30

MAX_TENTATIVAS = 5  # repeticoes para 5xx e falhas de rede
BACKOFF_INICIAL_SEGUNDOS = 1.0  # 1, 2, 4, 8, 16 s
MARGEM_RESET_SEGUNDOS = 5  # folga apos o horario de renovacao da cota
MAX_ESPERAS_COTA = 10  # protege contra laco infinito se a cota nunca renovar


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


class GraphQLError(RuntimeError):
    """Erro devolvido no campo `errors` de uma resposta GraphQL (ex.: repositorio inexistente)."""

    def __init__(self, erros: list[dict]) -> None:
        self.erros = erros
        super().__init__("; ".join(e.get("message", str(e)) for e in erros))

    @property
    def tipos(self) -> set[str]:
        return {e.get("type", "") for e in self.erros}


def _avisar_no_stderr(mensagem: str) -> None:
    print(mensagem, file=sys.stderr, flush=True)


class GitHubClient:
    """Cliente minimo da API REST do GitHub, com autenticacao, paginacao e
    tratamento de rate limit e erros temporarios."""

    def __init__(
        self,
        token: str | None = None,
        session: requests.Session | None = None,
        base_url: str = API_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_tentativas: int = MAX_TENTATIVAS,
        sleep: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.time,
        aviso: Callable[[str], None] = _avisar_no_stderr,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tentativas = max_tentativas
        self._sleep = sleep
        self._agora = agora
        self._aviso = aviso
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

    def _espera_por_limite(self, response: requests.Response) -> float | None:
        """Segundos a esperar se a resposta indica limite de requisicoes; None se nao."""
        if response.status_code not in (403, 429):
            return None
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            return float(retry_after)
        if response.headers.get("X-RateLimit-Remaining") == "0":
            reset = float(response.headers.get("X-RateLimit-Reset", self._agora()))
            return max(0.0, reset - self._agora()) + MARGEM_RESET_SEGUNDOS
        return None  # 403 que nao e de limite (ex.: lista de contribuidores grande demais)

    def _esperar_cota(self, segundos: float) -> None:
        retorno = datetime.fromtimestamp(self._agora() + segundos).strftime("%H:%M:%S")
        self._aviso(
            f"    Limite da API atingido: aguardando {segundos:.0f} s (ate {retorno}) "
            "para continuar..."
        )
        self._sleep(segundos)

    def _esperar_backoff(self, tentativa: int, motivo: str) -> None:
        segundos = BACKOFF_INICIAL_SEGUNDOS * 2**tentativa
        self._aviso(
            f"    {motivo}: nova tentativa em {segundos:.0f} s "
            f"({tentativa + 1}/{self.max_tentativas})..."
        )
        self._sleep(segundos)

    def _request(
        self, url: str, params: dict | None = None, corpo_json: dict | None = None
    ) -> requests.Response:
        """GET (ou POST, se `corpo_json` for dado) com espera de cota e backoff."""
        tentativas = 0  # erros 5xx e de rede ja repetidos nesta chamada
        esperas_cota = 0
        while True:
            try:
                if corpo_json is None:
                    response = self.session.get(url, params=params, timeout=self.timeout)
                else:
                    response = self.session.post(url, json=corpo_json, timeout=self.timeout)
            # ChunkedEncodingError: a conexao caiu no meio da resposta (nao e ConnectionError).
            except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError) as exc:
                if tentativas >= self.max_tentativas:
                    raise
                self._esperar_backoff(tentativas, f"Falha de rede ({type(exc).__name__})")
                tentativas += 1
                continue

            espera = self._espera_por_limite(response)
            if espera is not None and esperas_cota < MAX_ESPERAS_COTA:
                self._esperar_cota(espera)
                esperas_cota += 1
                continue

            if response.status_code >= 500 and tentativas < self.max_tentativas:
                self._esperar_backoff(tentativas, f"Erro temporario do GitHub ({response.status_code})")
                tentativas += 1
                continue

            response.raise_for_status()
            return response

    def get(self, path: str, params: dict | None = None) -> dict | list:
        """Faz um GET e devolve o JSON da resposta (uma unica pagina)."""
        return self.get_response(path, params).json()

    def get_response(self, path: str, params: dict | None = None) -> requests.Response:
        """Faz um GET e devolve a resposta inteira, para quem precisa dos cabecalhos."""
        return self._request(self._url(path), params)

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        """Executa uma consulta na API GraphQL e devolve o campo `data`.

        A cota da GraphQL e separada da REST. Quando ela acaba, a API pode
        responder 200 com um erro do tipo RATE_LIMITED, em vez de 403: nesse
        caso o cliente tambem espera a renovacao e repete. Outros erros viram
        `GraphQLError`.
        """
        corpo = {"query": query, "variables": variables or {}}
        esperas_cota = 0
        while True:
            response = self._request(self._url("/graphql"), corpo_json=corpo)
            payload = response.json()
            erros = payload.get("errors")
            if not erros:
                return payload["data"]
            erro = GraphQLError(erros)
            if "RATE_LIMITED" in erro.tipos and esperas_cota < MAX_ESPERAS_COTA:
                reset = float(response.headers.get("X-RateLimit-Reset", self._agora()))
                self._esperar_cota(max(0.0, reset - self._agora()) + MARGEM_RESET_SEGUNDOS)
                esperas_cota += 1
                continue
            raise erro

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
