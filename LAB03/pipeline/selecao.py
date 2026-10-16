"""Selecao de repositorios candidatos pela API de busca do GitHub.

A busca (`GET /search/repositories`) devolve no maximo 1.000 resultados por
consulta. Para obter mais candidatos, a busca e fatiada por faixas de estrelas
que descem: cada fatia e ordenada por estrelas (desc) e a proxima comeca na
menor contagem de estrelas vista na fatia anterior. Ex.:

    stars:>1000            -> 1.000 repos, o menor tem 52.310 estrelas
    stars:1001..52310      -> 1.000 repos, o menor tem 31.877 estrelas
    stars:1001..31877      -> ...

A fatia seguinte inclui o proprio limite (52.310) para nao perder repositorios
empatados nessa contagem; os repetidos sao descartados pelo `full_name`.

A API de busca tem cota propria (30 requisicoes/minuto com token), por isso
ha uma pausa entre as requisicoes.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

from pipeline.github_client import GitHubClient

SEARCH_PATH = "/search/repositories"
SEARCH_PER_PAGE = 100
SEARCH_MAX_PAGES = 10  # 10 paginas x 100 = teto de 1.000 resultados por consulta
SEARCH_PAUSE_SECONDS = 2.0  # 30 requisicoes/minuto

CANDIDATE_FIELDS = [
    "full_name",
    "owner",
    "name",
    "stargazers_count",
    "language",
    "created_at",
    "default_branch",
    "archived",
    "fork",
    "html_url",
]


def montar_faixa(estrelas_min: int, teto: int | None) -> str:
    """Monta o qualificador de estrelas da busca. `teto=None` e a primeira fatia."""
    if teto is None:
        return f"stars:>{estrelas_min}"
    return f"stars:{estrelas_min + 1}..{teto}"


def resumir_repositorio(item: dict) -> dict:
    """Mantem apenas os campos do resultado da busca usados pelo pipeline."""
    return {
        "full_name": item["full_name"],
        "owner": item["owner"]["login"],
        "name": item["name"],
        "stargazers_count": item["stargazers_count"],
        "language": item.get("language"),
        "created_at": item["created_at"],
        "default_branch": item["default_branch"],
        "archived": item.get("archived", False),
        "fork": item.get("fork", False),
        "html_url": item["html_url"],
    }


def buscar_candidatos(
    client: GitHubClient,
    estrelas_min: int,
    max_candidatos: int,
    pausa: float = SEARCH_PAUSE_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[list[dict], list[dict]]:
    """Busca repositorios com mais de `estrelas_min` estrelas, fatiando por faixas.

    Devolve `(candidatos, fatias)`: os candidatos (sem repeticoes, do mais para o
    menos estrelado) e um registro de cada fatia consultada, usado na Metodologia.
    """
    candidatos: dict[str, dict] = {}
    fatias: list[dict] = []
    teto: int | None = None
    primeira_requisicao = True

    while len(candidatos) < max_candidatos:
        faixa = montar_faixa(estrelas_min, teto)
        itens: list[dict] = []
        total_count = 0
        incompleto = False

        for pagina in range(1, SEARCH_MAX_PAGES + 1):
            if not primeira_requisicao:
                sleep(pausa)
            primeira_requisicao = False

            resposta = client.get(
                SEARCH_PATH,
                {
                    "q": faixa,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": SEARCH_PER_PAGE,
                    "page": pagina,
                },
            )
            total_count = resposta["total_count"]
            incompleto = incompleto or resposta.get("incomplete_results", False)
            itens.extend(resposta["items"])
            if len(resposta["items"]) < SEARCH_PER_PAGE:
                break

        novos = 0
        for item in itens:
            if item["full_name"] not in candidatos:
                candidatos[item["full_name"]] = resumir_repositorio(item)
                novos += 1

        fatias.append(
            {
                "faixa": faixa,
                "total_count": total_count,
                "resultados": len(itens),
                "novos": novos,
                "incompleto": incompleto,
            }
        )

        # A fatia coube inteira no teto de 1.000: nao ha mais repositorios a buscar.
        if not itens or total_count <= len(itens):
            break

        menor = min(item["stargazers_count"] for item in itens)
        # Se a fatia inteira tem a mesma contagem de estrelas, desce uma estrela
        # para nao repetir a mesma consulta para sempre.
        teto = menor - 1 if teto is not None and menor >= teto else menor
        if teto <= estrelas_min:
            break

    return list(candidatos.values())[:max_candidatos], fatias


def carregar_csv(caminho: str | Path) -> list[dict]:
    """Le um CSV gerado por `salvar_csv` (os valores voltam como texto)."""
    with Path(caminho).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def salvar_csv(linhas: list[dict], caminho: str | Path, campos: list[str]) -> Path:
    """Salva uma lista de dicionarios em CSV (UTF-8), criando a pasta se preciso."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)
    return caminho
