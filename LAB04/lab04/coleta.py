"""Coleta a amostra real de PRs: `python -m lab04.coleta`.

Roda à parte do estudo, porque depende da API do GitHub. O resultado fica versionado em
dados/prs.csv, e os critérios estão explicados em dados/README.md. A variável de ambiente
GITHUB_TOKEN é opcional.
"""

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

from lab04.config import criar_rng

REPOSITORIO = "TheHPXProject/hpx"
JANELA_SEM_BOT = "2026-03-01..2026-05-31"
JANELA_COM_BOT = "2026-07-01..2026-09-30"
MAX_HORAS_ATE_MERGE = 30 * 24
TAMANHO_AMOSTRA = 30
ARQUIVO_SAIDA = Path(__file__).parent.parent / "dados" / "prs.csv"

CODERABBIT = "coderabbitai[bot]"
SEM_COPILOT = "-reviewed-by:copilot-pull-request-reviewer[bot]"
PAUSA_ENTRE_BUSCAS = 7  # a busca sem token aceita 10 chamadas por minuto


def buscar_prs(filtros: str) -> list[dict]:
    """Retorna todos os PRs mergeados do repositório que atendem aos filtros."""
    consulta = f"repo:{REPOSITORIO} is:pr is:merged {SEM_COPILOT} {filtros}"
    cabecalhos = {"User-Agent": "lab04-coleta", "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        cabecalhos["Authorization"] = f"Bearer {token}"

    prs: list[dict] = []
    pagina = 1
    while True:
        parametros = urllib.parse.urlencode({"q": consulta, "per_page": 100, "page": pagina})
        requisicao = urllib.request.Request(
            f"https://api.github.com/search/issues?{parametros}", headers=cabecalhos
        )
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            corpo = json.load(resposta)
        time.sleep(PAUSA_ENTRE_BUSCAS)
        prs.extend(corpo["items"])
        if not corpo["items"] or len(prs) >= corpo["total_count"]:
            return prs
        pagina += 1


def horas_ate_merge(criado_em: str, merge_em: str) -> float:
    """Calcula as horas entre duas datas no formato ISO 8601 da API do GitHub."""
    diferenca = datetime.fromisoformat(merge_em) - datetime.fromisoformat(criado_em)
    return diferenca.total_seconds() / 3600


def montar_linhas(prs: list[dict], grupo: str, atuacao_bot: str) -> list[dict]:
    """Converte os PRs da API em linhas, mantendo só os de autores humanos no limite de tempo."""
    linhas = []
    for pr in prs:
        merge_em = pr["pull_request"]["merged_at"]
        horas = horas_ate_merge(pr["created_at"], merge_em)
        if pr["user"]["type"] == "Bot" or horas > MAX_HORAS_ATE_MERGE:
            continue
        linhas.append(
            {
                "pr": pr["number"],
                "grupo": grupo,
                "autor": pr["user"]["login"],
                "atuacao_bot": atuacao_bot,
                "criado_em": pr["created_at"],
                "merge_em": merge_em,
                "horas_ate_merge": round(horas, 2),
            }
        )
    return linhas


def sortear(linhas: list[dict], rng) -> pd.DataFrame:
    """Sorteia TAMANHO_AMOSTRA linhas, sem depender da ordem de retorno da API."""
    elegiveis = pd.DataFrame(linhas).sort_values("pr", ignore_index=True)
    sorteados = rng.choice(len(elegiveis), size=TAMANHO_AMOSTRA, replace=False)
    return elegiveis.iloc[sorteados].sort_values("pr")


def main() -> None:
    sem_bot = montar_linhas(
        buscar_prs(
            f"created:{JANELA_SEM_BOT} -reviewed-by:{CODERABBIT} -commenter:app/coderabbitai"
        ),
        "sem_bot",
        "nenhuma",
    )
    com_bot = montar_linhas(
        buscar_prs(f"created:{JANELA_COM_BOT} reviewed-by:{CODERABBIT}"), "com_bot", "review"
    ) + montar_linhas(
        buscar_prs(
            f"created:{JANELA_COM_BOT} -reviewed-by:{CODERABBIT} commenter:app/coderabbitai"
        ),
        "com_bot",
        "comentario",
    )
    print(f"Elegíveis: sem_bot={len(sem_bot)} com_bot={len(com_bot)}")

    rng = criar_rng()
    amostra = pd.concat([sortear(sem_bot, rng), sortear(com_bot, rng)])
    amostra.to_csv(ARQUIVO_SAIDA, index=False)
    print(f"{len(amostra)} PRs salvos em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
