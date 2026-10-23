"""Monta a planilha da amostra-ouro para a validacao manual (secao 6 do enunciado).

Este modulo so automatiza a parte **reproduzivel e mecanica** da validacao: o
sorteio dos 60 repositorios e de 5 releases por repositorio, com semente fixa, e
a montagem de uma planilha com link direto para cada release (a "dica" da
secao 6). As colunas de julgamento -- tipo do projeto, se as releases
representam entregas reais, e se cada release sorteada e corretiva -- saem
vazias: cada integrante preenche a sua copia de forma independente, sem
consultar os demais nem a saida da heuristica automatica (`metricas.cfr`).
"""

from __future__ import annotations

import random

CAMPOS_PLANILHA = [
    "full_name",
    "link_repositorio",
    "tipo_projeto",
    "releases_representam_entrega_real",
    "tag_name",
    "link_release",
    "corretiva",
]


def sortear_amostra_ouro(amostra: list[dict], n: int = 60, seed: int = 42) -> list[dict]:
    """Sorteia `n` repositorios da amostra final, com semente fixa e reproduzivel."""
    return random.Random(seed).sample(amostra, k=min(n, len(amostra)))


def sortear_releases(
    releases: list[dict], full_name: str, n: int = 5, seed: int = 42
) -> list[dict]:
    """Sorteia `n` releases de um repositorio, com semente fixa por repositorio.

    A semente combina `seed` com `full_name` para que cada repositorio tenha um
    sorteio proprio e reproduzivel, mas diferente dos demais.
    """
    rng = random.Random(f"{seed}:{full_name}")
    return rng.sample(releases, k=min(n, len(releases)))


def gerar_linhas_planilha(
    amostra_ouro: list[dict],
    releases_por_repo: dict[str, list[dict]],
    n_releases_por_repo: int = 5,
    seed: int = 42,
) -> list[dict]:
    """Monta uma linha por release sorteada, pronta para `pipeline.selecao.salvar_csv`.

    `releases_por_repo` mapeia `full_name -> releases principais da janela`
    (ver `pipeline.releases.releases_principais`/`releases_na_janela`).
    """
    linhas = []
    for repo in amostra_ouro:
        full_name = repo["full_name"]
        releases = sortear_releases(
            releases_por_repo.get(full_name, []), full_name, n_releases_por_repo, seed
        )
        if not releases:
            linhas.append(
                {
                    "full_name": full_name,
                    "link_repositorio": f"https://github.com/{full_name}",
                    "tipo_projeto": "",
                    "releases_representam_entrega_real": "",
                    "tag_name": "",
                    "link_release": "",
                    "corretiva": "",
                }
            )
            continue
        for release in releases:
            linhas.append(
                {
                    "full_name": full_name,
                    "link_repositorio": f"https://github.com/{full_name}",
                    "tipo_projeto": "",
                    "releases_representam_entrega_real": "",
                    "tag_name": release["tag_name"],
                    "link_release": f"https://github.com/{full_name}/releases/tag/{release['tag_name']}",
                    "corretiva": "",
                }
            )
    return linhas


# ---------------------------------------------------------------------------
# Pagina de rotulagem (comando `python -m pipeline.amostra_ouro`)
# ---------------------------------------------------------------------------
#
# Para cada release sorteada, busca as release notes e as mensagens dos commits
# entre ela e a release anterior, e gera:
# - `dados_rotulagem.json`: dados completos, usados depois por
#   `analise/amostra_ouro.py` para avaliar a heuristica;
# - `pagina_rotulagem.html`: pagina local que mostra as notas e os commits
#   (resumidos) e coleta os rotulos. A pagina NAO mostra a saida da heuristica,
#   para nao influenciar quem rotula (secao 6 do enunciado).

import argparse  # noqa: E402
import html  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import requests  # noqa: E402

MAX_COMMITS_NA_PAGINA = 80
MAX_CARACTERES_NOTAS = 4000


def release_anterior(historico: list[dict], tag_name: str) -> str | None:
    """Tag da release que vem antes de `tag_name` no historico cronologico."""
    tags = [r["tag_name"] for r in historico]
    indice = tags.index(tag_name)
    return tags[indice - 1] if indice > 0 else None


def coletar_dados_release(client, full_name: str, release: dict, tag_anterior: str | None) -> dict:
    """Release notes e mensagens de commit de uma release sorteada."""
    from pipeline.commits import comparar_commits, mensagens_de_commit

    notas = ""
    try:
        notas = client.get(f"/repos/{full_name}/releases/tags/{release['tag_name']}").get("body") or ""
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 404:
            raise

    mensagens: list[str] = []
    compare_ok = tag_anterior is not None
    if tag_anterior:
        try:
            mensagens = mensagens_de_commit(comparar_commits(client, full_name, tag_anterior, release["tag_name"]))
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code != 404:
                raise
            compare_ok = False

    return {
        "full_name": full_name,
        "tag_name": release["tag_name"],
        "tag_anterior": tag_anterior,
        "published_at": release["published_at"],
        "link_release": f"https://github.com/{full_name}/releases/tag/{release['tag_name']}",
        "notas": notas,
        "mensagens_commits": mensagens,
        "compare_ok": compare_ok,
    }


def dados_para_pagina(dados: list[dict]) -> list[dict]:
    """Versao resumida para a pagina: primeira linha dos commits e notas cortadas."""
    resumidos = []
    for d in dados:
        linhas = [m.splitlines()[0] if m else "" for m in d["mensagens_commits"]]
        resumidos.append(
            {
                "full_name": d["full_name"],
                "tag_name": d["tag_name"],
                "tag_anterior": d["tag_anterior"],
                "published_at": d["published_at"],
                "link_release": d["link_release"],
                "notas": d["notas"][:MAX_CARACTERES_NOTAS],
                "notas_cortadas": len(d["notas"]) > MAX_CARACTERES_NOTAS,
                "commits": linhas[:MAX_COMMITS_NA_PAGINA],
                "n_commits": len(linhas),
                "compare_ok": d["compare_ok"],
            }
        )
    return resumidos


def gerar_pagina(dados: list[dict], avaliador: str) -> str:
    """HTML autocontido da pagina de rotulagem."""
    modelo = (Path(__file__).parent / "pagina_rotulagem.html").read_text(encoding="utf-8")
    conteudo = json.dumps(dados_para_pagina(dados), ensure_ascii=False).replace("</", "<\\/")
    return modelo.replace("__DADOS__", conteudo).replace("__AVALIADOR__", html.escape(avaliador))


def main(argv: list[str] | None = None) -> int:
    from pipeline.config import load_config
    from pipeline.github_client import GitHubClient
    from pipeline.releases import releases_na_janela, releases_principais
    from pipeline.selecao import carregar_csv

    parser = argparse.ArgumentParser(prog="pipeline.amostra_ouro", description="Gera a pagina de rotulagem da amostra-ouro.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--n-repos", type=int, default=60, help="Repositorios rotulados (60 no protocolo completo)")
    parser.add_argument("--releases-por-repo", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--avaliador", default="avaliador")
    parser.add_argument("--saida", default="resultados/amostra_ouro")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    resultados_dir = Path(config.get("resultados_dir", "resultados"))
    cache_dir = Path(config.get("cache_dir", "cache"))
    inicio, fim = config["janela"]["inicio"], config["janela"]["fim"]
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    caminho_dados = saida / "dados_rotulagem.json"

    if caminho_dados.exists():
        dados = json.loads(caminho_dados.read_text(encoding="utf-8"))
        print(f"Reaproveitando {len(dados)} releases de {caminho_dados}")
    else:
        amostra = carregar_csv(resultados_dir / "amostra.csv")
        # Os n primeiros do sorteio de 60: uma amostra menor e um prefixo da completa.
        sorteados = sortear_amostra_ouro(amostra, n=60, seed=args.seed)[: args.n_repos]
        client = GitHubClient()
        dados = []
        for i, repo in enumerate(sorteados, start=1):
            full_name = repo["full_name"]
            caminho = cache_dir / "releases" / f"{full_name.replace('/', '__')}.json"
            historico = releases_principais(json.loads(caminho.read_text(encoding="utf-8")))
            da_janela = releases_na_janela(historico, inicio, fim)
            for release in sortear_releases(da_janela, full_name, args.releases_por_repo, args.seed):
                anterior = release_anterior(historico, release["tag_name"])
                dados.append(coletar_dados_release(client, full_name, release, anterior))
            print(f"    {i}/{len(sorteados)} {full_name}")
        caminho_dados.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    caminho_pagina = saida / "pagina_rotulagem.html"
    caminho_pagina.write_text(gerar_pagina(dados, args.avaliador), encoding="utf-8")
    n_repos = len({d["full_name"] for d in dados})
    print(f"{len(dados)} releases de {n_repos} repositorios. Abra no navegador: {caminho_pagina.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
