"""Coleta de commits entre releases (`GET /repos/{full_name}/compare/{base}...{head}`),
usada para calcular o lead time (RQ 02).

Para cada release R da janela (exceto a primeira da historia do repositorio,
que nao tem release anterior), os commits incluidos sao obtidos comparando R
com a release anterior -- que pode estar fora da janela (secao 5, RQ 02). Por
isso a coleta recebe o historico completo de releases principais e a janela,
e nao so as releases da janela. O resultado e uma lista no formato esperado por
`metricas.lead_time.lead_time_repositorio` e por `metricas.cfr.cfr_repositorio`
(que usa `tag_anterior` e `mensagens_commits` para a heuristica de release
corretiva).

O endpoint de comparacao nao pagina oficialmente, mas devolve no maximo 250
commits por chamada (secao 4 do enunciado); `comparar_commits` insiste com
`per_page`/`page` ate esgotar.

O compare e a chamada mais cara da coleta (uma por release). As tres unidades de
deploy da RQ 07 (release, release + pre-release e tag) repetem muitos pares
`base...head` -- a maioria das tags sao as proprias releases --, entao o
resultado de cada par fica num cache por repositorio (`cache_dir/compares/`),
compartilhado entre elas: um par ja comparado nunca e pedido de novo a API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import requests

from pipeline.criterio_inclusao import Janela, parse_data
from pipeline.github_client import GitHubClient
from pipeline.retomada import TRABALHADORES_PADRAO, gravar_json, processar_em_paralelo

CACHE_SUBDIR = "commits_entre_releases"
CACHE_COMPARES_SUBDIR = "compares"
SALVAR_COMPARES_A_CADA = 50  # protege repositorios com muitas releases contra interrupcao
COMMITS_POR_PAGINA = 250

MOTIVO_PRIMEIRA_RELEASE = "primeira_release"
MOTIVO_COMPARE_404 = "compare_404"


def _caminho_cache(cache_dir: str | Path, full_name: str, subdir: str = CACHE_SUBDIR) -> Path:
    return Path(cache_dir) / subdir / f"{full_name.replace('/', '__')}.json"


class CacheCompares:
    """Resultado de cada par `base...head` de um repositorio, gravado em disco.

    Guarda as datas de autor e as mensagens dos commits, ou o status HTTP 404
    quando o par nao pode ser comparado (tag apagada ou reescrita).
    """

    def __init__(self, caminho: Path | None = None) -> None:
        self.caminho = caminho
        self.pares: dict[str, dict] = {}
        if caminho is not None and caminho.exists():
            self.pares = json.loads(caminho.read_text(encoding="utf-8"))
        self._novos = 0

    def obter(self, client: GitHubClient, full_name: str, base: str, head: str) -> dict:
        chave = f"{base}...{head}"
        if chave not in self.pares:
            try:
                commits = comparar_commits(client, full_name, base, head)
                self.pares[chave] = {
                    "datas": datas_de_autor(commits),
                    "mensagens": mensagens_de_commit(commits),
                }
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code != 404:
                    raise
                self.pares[chave] = {"status": 404}
            self._novos += 1
            if self._novos % SALVAR_COMPARES_A_CADA == 0:
                self.salvar()
        return self.pares[chave]

    def salvar(self) -> None:
        if self.caminho is None or not self._novos:
            return
        gravar_json(self.caminho, self.pares)


def comparar_commits(client: GitHubClient, full_name: str, base: str, head: str) -> list[dict]:
    """Devolve os commits entre `base` (exclusive) e `head` (inclusive)."""
    commits: list[dict] = []
    pagina = 1
    while True:
        resposta = client.get(
            f"/repos/{full_name}/compare/{base}...{head}",
            {"per_page": COMMITS_POR_PAGINA, "page": pagina},
        )
        pagina_commits = resposta["commits"]
        commits.extend(pagina_commits)
        if len(pagina_commits) < COMMITS_POR_PAGINA:
            break
        pagina += 1
    return commits


def datas_de_autor(commits: list[dict]) -> list[str]:
    """Extrai `commit.author.date` de cada commit retornado pelo compare."""
    return [c["commit"]["author"]["date"] for c in commits]


def mensagens_de_commit(commits: list[dict]) -> list[str]:
    """Extrai `commit.message` de cada commit retornado pelo compare.

    Usada pela heuristica de release corretiva (`metricas.cfr`), que procura
    `revert`/`hotfix`/`fix` nas mensagens. `.get` com default vazio porque
    commits muito antigos no cache (coletados antes desta mensagem existir)
    podem nao ter o campo.
    """
    return [c.get("commit", {}).get("message", "") for c in commits]


def montar_releases_com_commits(
    client: GitHubClient,
    full_name: str,
    releases_ordenadas: list[dict],
    janela: Janela | None = None,
    compares: CacheCompares | None = None,
) -> tuple[list[dict], dict[str, int]]:
    """Monta, para cada release da janela com release anterior, a lista de commits incluidos.

    `releases_ordenadas` deve conter o historico completo das releases da
    definicao principal (ver `pipeline.releases.releases_principais`), em ordem
    cronologica, e nao so as da janela: a release anterior a primeira release da
    janela costuma estar fora dela e e a base do compare. So as releases dentro
    de `janela` sao comparadas; sem `janela`, todas sao.

    Devolve `(releases_com_commits, motivos_ignoradas)`: as releases prontas
    para `metricas.lead_time.lead_time_repositorio` e a contagem de releases
    da janela ignoradas por motivo, usada no funil/ameacas a validade.
    `compares` reaproveita pares ja comparados (ver `CacheCompares`).
    """
    compares = compares or CacheCompares()
    resultado: list[dict] = []
    motivos = {MOTIVO_PRIMEIRA_RELEASE: 0, MOTIVO_COMPARE_404: 0}

    def na_janela(release: dict) -> bool:
        if janela is None:
            return True
        return bool(release["published_at"]) and janela.contem(parse_data(release["published_at"]))

    if releases_ordenadas and na_janela(releases_ordenadas[0]):
        motivos[MOTIVO_PRIMEIRA_RELEASE] = 1

    for anterior, atual in zip(releases_ordenadas, releases_ordenadas[1:]):
        if not na_janela(atual):
            continue
        par = compares.obter(client, full_name, anterior["tag_name"], atual["tag_name"])
        if par.get("status") == 404:
            motivos[MOTIVO_COMPARE_404] += 1
            continue
        resultado.append(
            {
                "tag_name": atual["tag_name"],
                "tag_anterior": anterior["tag_name"],
                "published_at": atual["published_at"],
                "commits": par["datas"],
                "mensagens_commits": par["mensagens"],
            }
        )

    return resultado, motivos


def coletar_commits_entre_releases(
    client: GitHubClient,
    repositorios: dict[str, list[dict]],
    cache_dir: str | Path,
    progresso: Callable[[int, int], None] | None = None,
    janela: Janela | None = None,
    subdir: str = CACHE_SUBDIR,
    trabalhadores: int = TRABALHADORES_PADRAO,
) -> dict[str, dict]:
    """Para cada repositorio, monta as releases com commits, reaproveitando o cache.

    `repositorios` mapeia `full_name -> historico de releases principais
    ordenadas` (ja filtradas por `releases_principais`, sem cortar pela janela).
    Devolve `full_name -> {"releases": [...], "motivos_ignoradas": {...}}`.

    O cache guarda a janela usada; um cache de outra janela (ou de uma versao
    anterior do pipeline, que nao a registrava) e refeito. `subdir` separa o
    cache de cada unidade de deploy (release, release + pre-release, tag) da RQ 07:
    a mesma funcao serve as tres, so muda a lista de "releases" recebida.
    Os repositorios pendentes sao processados `trabalhadores` por vez.
    """
    cache_dir = Path(cache_dir)
    chave_janela = janela.filtro_created() if janela else None
    resultado: dict[str, dict] = {}
    pendentes = []
    for full_name in repositorios:
        caminho = _caminho_cache(cache_dir, full_name, subdir)
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            if dados.get("janela") == chave_janela:
                resultado[full_name] = dados
                continue
        pendentes.append(full_name)

    def processar(client_thread: GitHubClient, full_name: str) -> None:
        compares = CacheCompares(_caminho_cache(cache_dir, full_name, CACHE_COMPARES_SUBDIR))
        try:
            releases, motivos = montar_releases_com_commits(
                client_thread, full_name, repositorios[full_name], janela, compares
            )
        finally:
            # Grava os pares ja comparados mesmo se a coleta parar no meio do repositorio.
            compares.salvar()
        dados = {"janela": chave_janela, "releases": releases, "motivos_ignoradas": motivos}
        gravar_json(_caminho_cache(cache_dir, full_name, subdir), dados)
        resultado[full_name] = dados

    processar_em_paralelo(pendentes, processar, client, trabalhadores, progresso)

    return {full_name: resultado[full_name] for full_name in repositorios}
