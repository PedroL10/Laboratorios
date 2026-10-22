"""Coleta de workflow runs (`GET /repos/{full_name}/actions/runs`), usada no
CFR variante (a) e no tempo de recuperacao (RQ 03 e RQ 04).

Sao coletados os runs do default branch disparados por push (`event=push`) e
criados dentro da janela (secao 3 do enunciado). A classificacao por
`conclusion` (sucesso, falha ou ignorado) fica em `metricas`, entao aqui todos
os runs sao guardados, inclusive os que serao ignorados.

Com filtros, a API devolve no maximo 1.000 runs por consulta (secao 4). Por
isso a janela e dividida em meses; antes de paginar uma fatia, o `total_count`
dela e consultado (com `per_page=1`) e, se passar de 1.000, a fatia e dividida
ao meio, ate caber ou chegar a um unico dia. Um dia que ainda passa do teto e
coletado ate o limite e contado em `fatias_no_teto` (os runs dele ficam
incompletos, o que vai para as ameacas a validade).

Cada repositorio tem os seus runs cacheados num JSON proprio em
`cache_dir/workflow_runs/`, gravado so quando o repositorio termina: uma coleta
interrompida refaz apenas o repositorio em andamento.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from pipeline.criterio_inclusao import Janela
from pipeline.github_client import GitHubClient

CACHE_SUBDIR = "workflow_runs"
TETO_POR_CONSULTA = 1000  # maximo de resultados de uma consulta filtrada
RUNS_POR_PAGINA = 100

# Campos de cada run usados pelas metricas; o resto da resposta e descartado.
CAMPOS_RUN = (
    "id",
    "workflow_id",
    "name",
    "conclusion",
    "created_at",
    "run_started_at",
    "updated_at",
)


def _caminho_cache(cache_dir: str | Path, full_name: str) -> Path:
    return Path(cache_dir) / CACHE_SUBDIR / f"{full_name.replace('/', '__')}.json"


def fatias_mensais(janela: Janela) -> list[tuple[date, date]]:
    """Divide a janela em meses de calendario, com inicio e fim inclusivos."""
    fatias = []
    inicio = janela.inicio_data
    while inicio <= janela.fim_data:
        proximo_mes = (inicio.replace(day=1) + timedelta(days=32)).replace(day=1)
        fim = min(proximo_mes - timedelta(days=1), janela.fim_data)
        fatias.append((inicio, fim))
        inicio = fim + timedelta(days=1)
    return fatias


def _filtro_created(inicio: date, fim: date) -> str:
    return f"{inicio.isoformat()}..{fim.isoformat()}"


def _resumir_run(run: dict) -> dict:
    return {campo: run.get(campo) for campo in CAMPOS_RUN}


def coletar_runs_repositorio(
    client: GitHubClient, full_name: str, branch: str, janela: Janela
) -> tuple[list[dict], int]:
    """Coleta os runs de push do `branch` na janela, fatia por fatia.

    Devolve `(runs, fatias_no_teto)`: os runs em ordem cronologica de criacao,
    sem repeticoes, e quantas fatias de um dia passaram do teto de 1.000.
    """
    path = f"/repos/{full_name}/actions/runs"
    base = {"branch": branch, "event": "push"}
    runs: dict[int, dict] = {}
    fatias_no_teto = 0

    pendentes = fatias_mensais(janela)
    while pendentes:
        inicio, fim = pendentes.pop(0)
        params = {**base, "created": _filtro_created(inicio, fim)}
        total = client.get(path, {**params, "per_page": 1})["total_count"]
        if total == 0:
            continue
        if total > TETO_POR_CONSULTA:
            if inicio < fim:
                meio = inicio + (fim - inicio) // 2
                pendentes[:0] = [(inicio, meio), (meio + timedelta(days=1), fim)]
                continue
            fatias_no_teto += 1

        for run in client.get_paginated(
            path,
            {**params, "per_page": RUNS_POR_PAGINA},
            items_key="workflow_runs",
            max_pages=TETO_POR_CONSULTA // RUNS_POR_PAGINA,
        ):
            runs[run["id"]] = _resumir_run(run)

    ordenados = sorted(runs.values(), key=lambda r: (r["created_at"] or "", r["id"]))
    return ordenados, fatias_no_teto


def coletar_workflow_runs(
    client: GitHubClient,
    repositorios: list[dict],
    janela: Janela,
    cache_dir: str | Path,
    progresso: Callable[[int, int], None] | None = None,
) -> dict[str, dict]:
    """Coleta os runs de varios repositorios, reaproveitando o cache existente.

    `repositorios` sao linhas da amostra, com `full_name` e `default_branch`.
    Devolve `full_name -> {"janela", "runs", "fatias_no_teto"}`, na ordem de
    entrada. Um cache de outra janela e refeito.
    """
    cache_dir = Path(cache_dir)
    chave_janela = janela.filtro_created()
    resultado: dict[str, dict] = {}
    pendentes = []
    for repo in repositorios:
        caminho = _caminho_cache(cache_dir, repo["full_name"])
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if dados.get("janela") == chave_janela:
                resultado[repo["full_name"]] = dados
                continue
        pendentes.append(repo)

    for i, repo in enumerate(pendentes, start=1):
        runs, fatias_no_teto = coletar_runs_repositorio(
            client, repo["full_name"], repo["default_branch"], janela
        )
        dados = {"janela": chave_janela, "runs": runs, "fatias_no_teto": fatias_no_teto}
        caminho = _caminho_cache(cache_dir, repo["full_name"])
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        resultado[repo["full_name"]] = dados
        if progresso:
            progresso(i, len(pendentes))

    return {repo["full_name"]: resultado[repo["full_name"]] for repo in repositorios}
