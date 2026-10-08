"""Criterio minimo de inclusao (secao 3 do enunciado).

Um repositorio entra na amostra se tiver, dentro da janela de observacao:
- pelo menos `min_releases` releases publicadas (draft = false, prerelease = false); e
- pelo menos `min_runs` workflow runs validos no default branch, disparados por push.
  Run valido e o que tem `conclusion` de sucesso (success) ou de falha
  (failure, timed_out, startup_failure); os demais sao ignorados.

Para economizar cota, os runs sao contados pelo `total_count` de consultas com
`per_page=1`, filtradas por status. O filtro de status da API nao aceita
`startup_failure`; por isso, quando a soma fica abaixo do minimo, os runs sao
listados e contados um a um antes de descartar o repositorio.

A API limita o `total_count` dos runs a 2.500. Em repositorios muito ativos as
contagens saturam nesse teto (cada uma separadamente), entao a soma dos validos
pode passar do total de push. Isso nao afeta o criterio (2.500 >> 50), mas a
coluna `runs_no_teto` marca esses casos: os numeros sao limites inferiores.

Os candidatos sao avaliados na ordem do CSV (mais estrelados primeiro) ate a
amostra atingir `n_repos` repositorios incluidos.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Callable

import requests

from pipeline.github_client import GitHubClient, erro_transitorio, status_http
from pipeline.retomada import processar_com_retomada

CRITERIO_FIELDS = [
    "full_name",
    "n_releases_janela",
    "n_runs_push",
    "n_runs_validos",
    "runs_no_teto",
    "incluido",
    "motivo_descarte",
]

CONCLUSOES_SUCESSO = {"success"}
CONCLUSOES_FALHA = {"failure", "timed_out", "startup_failure"}
CONCLUSOES_VALIDAS = CONCLUSOES_SUCESSO | CONCLUSOES_FALHA
# Status aceitos pelo filtro `status` da API (startup_failure nao e aceito).
STATUS_FILTRAVEIS = ("success", "failure", "timed_out")

# Releases vem da mais nova para a mais antiga. Depois desta quantidade de
# releases seguidas criadas antes da janela, a paginacao para.
RELEASES_ANTIGAS_PARA_PARAR = 100

RUNS_MAX_PAGINAS = 10  # teto de 1.000 resultados por consulta filtrada
TETO_TOTAL_COUNT_RUNS = 2500  # maior total_count que a API devolve para runs


class Janela:
    """Janela de observacao, com inicio e fim inclusivos (datas em UTC)."""

    def __init__(self, inicio: str | date, fim: str | date) -> None:
        self.inicio_data = date.fromisoformat(str(inicio))
        self.fim_data = date.fromisoformat(str(fim))
        if self.inicio_data > self.fim_data:
            raise ValueError("O inicio da janela deve ser anterior ao fim.")
        self.inicio = datetime.combine(self.inicio_data, time.min, tzinfo=timezone.utc)
        self.fim = datetime.combine(self.fim_data, time.max, tzinfo=timezone.utc)

    def contem(self, momento: datetime) -> bool:
        return self.inicio <= momento <= self.fim

    def filtro_created(self) -> str:
        """Qualificador `created` da API de workflow runs (AAAA-MM-DD..AAAA-MM-DD)."""
        return f"{self.inicio_data.isoformat()}..{self.fim_data.isoformat()}"


def parse_data(valor: str) -> datetime:
    """Converte datas da API (ex.: 2025-10-03T12:00:00Z) em datetime com fuso UTC."""
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def contar_releases_na_janela(client: GitHubClient, full_name: str, janela: Janela) -> int:
    """Conta releases publicadas (sem draft e sem pre-release) dentro da janela."""
    n = 0
    antigas_seguidas = 0
    for release in client.get_paginated(f"/repos/{full_name}/releases"):
        if parse_data(release["created_at"]) < janela.inicio:
            antigas_seguidas += 1
            if antigas_seguidas >= RELEASES_ANTIGAS_PARA_PARAR:
                break
        else:
            antigas_seguidas = 0

        if release.get("draft") or release.get("prerelease") or not release.get("published_at"):
            continue
        if janela.contem(parse_data(release["published_at"])):
            n += 1
    return n


def contar_runs(
    client: GitHubClient, full_name: str, branch: str, janela: Janela, minimo: int
) -> tuple[int, int | None]:
    """Devolve `(n_runs_push, n_runs_validos)` do default branch na janela.

    Se ha menos de `minimo` runs de push no total, os validos nao sao contados
    (sao no maximo o total) e `n_runs_validos` volta como None.
    """
    path = f"/repos/{full_name}/actions/runs"
    base = {"branch": branch, "event": "push", "created": janela.filtro_created()}

    n_push = client.get(path, {**base, "per_page": 1})["total_count"]
    if n_push < minimo:
        return n_push, None

    n_validos = sum(
        client.get(path, {**base, "status": status, "per_page": 1})["total_count"]
        for status in STATUS_FILTRAVEIS
    )
    if n_validos < minimo and n_push > n_validos:
        # Pode haver startup_failure, que o filtro de status nao alcanca: conta um a um.
        n_validos = sum(
            1
            for run in client.get_paginated(
                path, base, items_key="workflow_runs", max_pages=RUNS_MAX_PAGINAS
            )
            if run.get("conclusion") in CONCLUSOES_VALIDAS
        )
    return n_push, n_validos


def avaliar_repositorio(
    client: GitHubClient,
    repo: dict,
    janela: Janela,
    min_releases: int,
    min_runs: int,
) -> dict:
    """Aplica o criterio de inclusao a um repositorio e devolve a linha do CSV."""
    linha = {
        "full_name": repo["full_name"],
        "n_releases_janela": None,
        "n_runs_push": None,
        "n_runs_validos": None,
        "runs_no_teto": False,
        "incluido": False,
        "motivo_descarte": "",
    }
    try:
        linha["n_releases_janela"] = contar_releases_na_janela(client, repo["full_name"], janela)
        if linha["n_releases_janela"] < min_releases:
            linha["motivo_descarte"] = f"menos_de_{min_releases}_releases"
            return linha

        n_push, n_validos = contar_runs(
            client, repo["full_name"], repo["default_branch"], janela, min_runs
        )
        linha["n_runs_push"], linha["n_runs_validos"] = n_push, n_validos
        linha["runs_no_teto"] = n_push >= TETO_TOTAL_COUNT_RUNS
        if n_validos is None or n_validos < min_runs:
            linha["motivo_descarte"] = f"menos_de_{min_runs}_runs_validos"
            return linha
    except requests.HTTPError as exc:
        # Cota esgotada ou erro temporario nao e descarte: interrompe para retomar depois.
        if erro_transitorio(exc):
            raise
        linha["motivo_descarte"] = f"erro_http_{status_http(exc)}"
        return linha

    linha["incluido"] = True
    return linha


def incluido(linha: dict) -> bool:
    """Le a coluna `incluido`, que vem como texto quando carregada do CSV."""
    return str(linha["incluido"]) == "True"


def aplicar_criterio(
    client: GitHubClient,
    repositorios: list[dict],
    janela: Janela,
    min_releases: int,
    min_runs: int,
    n_repos: int | None,
    caminho_saida: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Avalia os repositorios em ordem ate incluir `n_repos` (ou todos, se None).

    Devolve as linhas dos repositorios avaliados, na ordem de `repositorios`.
    Os que nao chegaram a ser avaliados nao aparecem no resultado.
    """
    def amostra_completa(anteriores: list[dict]) -> bool:
        return n_repos is not None and sum(map(incluido, anteriores)) >= n_repos

    def reportar(feitos: int) -> None:
        if progresso:
            progresso(feitos, len(repositorios))

    processados = processar_com_retomada(
        repositorios,
        lambda repo: avaliar_repositorio(client, repo, janela, min_releases, min_runs),
        caminho_saida,
        CRITERIO_FIELDS,
        progresso=reportar,
        parar=amostra_completa,
    )

    avaliados = [processados[r["full_name"]] for r in repositorios if r["full_name"] in processados]
    if n_repos is not None:
        # Numa retomada o CSV pode ter mais incluidos que o pedido: corta no n-esimo.
        cortados, n_incluidos = [], 0
        for linha in avaliados:
            if n_incluidos >= n_repos:
                break
            cortados.append(linha)
            n_incluidos += incluido(linha)
        avaliados = cortados
    return avaliados
