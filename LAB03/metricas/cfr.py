"""Calculo da change failure rate (CFR), variante (b) - proxy de entrega (RQ 03).

Uma release R e considerada **falha** se for seguida, em ate 7 dias, por uma
**release corretiva**. A heuristica automatica de release corretiva (secao 3,
RQ 03) combina duas pistas:

- a versao muda apenas no numero de *patch* do Versionamento Semantico
  (`2.3.0 -> 2.3.1`); e/ou
- ha commits com `revert`, `hotfix` ou `fix` na mensagem entre as duas releases.

Cada release e representada por um dicionario:

    {
        "tag_name": "v2.3.1",
        "tag_anterior": "v2.3.0",       # None para a primeira release da historia
        "published_at": "2024-05-12T00:00:00Z",
        "mensagens_commits": ["fix: crash ao abrir arquivo", ...],
    }

`mensagens_commits` traz a mensagem de cada commit incluido nesta release
(obtidos comparando-a com `tag_anterior`), usada para a pista de palavra-chave.
Releases sem release anterior (a primeira da historia) nao podem ser
classificadas como corretivas, por falta de versao anterior para comparar.

Esta heuristica precisa ser validada contra a amostra rotulada manualmente
(secao 6) antes de ser usada nas conclusoes do artigo: ver `avaliar_heuristica`.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timezone

PALAVRAS_CHAVE_CORRETIVA = ("revert", "hotfix", "fix")

JANELA_CORRECAO_DIAS = 7
JANELA_CENSURA_DIAS = 7

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def _parse(data_iso: str) -> datetime:
    return datetime.fromisoformat(data_iso.replace("Z", "+00:00"))


def _fim_da_janela(fim_janela: str) -> datetime:
    """Fim da janela em UTC; uma data sem horario (AAAA-MM-DD, como no config.yaml)
    vale ate o fim daquele dia, como em `pipeline.criterio_inclusao.Janela`."""
    if len(fim_janela) == 10:
        return datetime.combine(date.fromisoformat(fim_janela), time.max, tzinfo=timezone.utc)
    return _parse(fim_janela)


def _parse_semver(tag_name: str) -> tuple[int, int, int] | None:
    """Extrai (major, minor, patch) de uma tag, ou None se nao for SemVer."""
    match = _SEMVER_RE.match(tag_name)
    if not match:
        return None
    return tuple(int(g) for g in match.groups())  # type: ignore[return-value]


def eh_patch_only(tag_anterior: str | None, tag_atual: str) -> bool:
    """True se `tag_atual` muda so o numero de patch em relacao a `tag_anterior`."""
    if tag_anterior is None:
        return False
    anterior = _parse_semver(tag_anterior)
    atual = _parse_semver(tag_atual)
    if anterior is None or atual is None:
        return False
    return anterior[0] == atual[0] and anterior[1] == atual[1] and anterior[2] != atual[2]


def titulo(mensagem: str) -> str:
    """Primeira linha (titulo) de uma mensagem de commit."""
    return mensagem.split("\n", 1)[0] if mensagem else ""


def tem_commit_com_palavra_chave(mensagens_commits: list[str]) -> bool:
    """True se o titulo (primeira linha) de algum commit contem `revert`, `hotfix` ou `fix`.

    So o titulo e considerado: e onde convencoes como `fix:` e `Revert "..."`
    aparecem, e guardar o corpo de cada commit tornava os caches grandes demais
    para a memoria (gigabytes em repositorios como o ClickHouse).
    """
    return any(
        palavra in titulo(mensagem).lower()
        for mensagem in mensagens_commits
        for palavra in PALAVRAS_CHAVE_CORRETIVA
    )


def eh_corretiva(release: dict) -> bool:
    """Classifica uma release como corretiva pela heuristica automatica.

    Combina as duas pistas da secao 3: patch-only no SemVer e/ou palavra-chave
    nas mensagens de commit. Basta uma das duas ser verdadeira.
    """
    return eh_patch_only(release.get("tag_anterior"), release["tag_name"]) or (
        tem_commit_com_palavra_chave(release.get("mensagens_commits") or [])
    )


def classificar_releases(releases: list[dict]) -> list[dict]:
    """Devolve `releases` com o campo `corretiva` adicionado a cada uma."""
    return [{**r, "corretiva": eh_corretiva(r)} for r in releases]


def cfr_repositorio(releases: list[dict], fim_janela: str) -> dict:
    """CFR variante (b) de um repositorio: proporcao de releases que falharam.

    `releases` deve estar em ordem cronologica e conter todas as releases
    principais da janela (ver `pipeline.releases.releases_principais` e
    `releases_na_janela`). Uma release R falha se a release seguinte, dentro
    de ate `JANELA_CORRECAO_DIAS` dias, for corretiva pela heuristica.

    Releases publicadas nos ultimos `JANELA_CENSURA_DIAS` dias da janela nao
    sao avaliadas (ainda nao se sabe se havera correcao) e ficam de fora do
    denominador; `n_censuradas` conta quantas foram essas.
    """
    classificadas = classificar_releases(releases)
    limite_censura = _fim_da_janela(fim_janela)

    n_avaliadas = 0
    n_falhas = 0
    n_censuradas = 0

    for i, atual in enumerate(classificadas):
        publicada_em = _parse(atual["published_at"])
        dias_ate_fim = (limite_censura - publicada_em).total_seconds() / 86400
        if dias_ate_fim < JANELA_CENSURA_DIAS:
            n_censuradas += 1
            continue

        n_avaliadas += 1
        proxima = classificadas[i + 1] if i + 1 < len(classificadas) else None
        if proxima is not None:
            dias_para_proxima = (
                _parse(proxima["published_at"]) - publicada_em
            ).total_seconds() / 86400
            if dias_para_proxima <= JANELA_CORRECAO_DIAS and proxima["corretiva"]:
                n_falhas += 1

    return {
        "cfr_entrega": (n_falhas / n_avaliadas) if n_avaliadas else None,
        "n_releases_avaliadas": n_avaliadas,
        "n_releases_falhas": n_falhas,
        "n_releases_censuradas": n_censuradas,
    }


def rework_repositorio(releases: list[dict]) -> dict:
    """Deployment rework rate (RQ 08, bonus): releases corretivas / releases.

    Metrica acrescentada pelo DORA em 2024: proporcao de deploys nao
    planejados, feitos para corrigir problemas. Usa a mesma heuristica de
    release corretiva do CFR (b), mas sem a janela de 7 dias nem a ligacao com
    a release anterior: conta toda release corretiva. Por isso nao ha censura.
    `releases` sao as releases da janela com release anterior (as que tem
    `tag_anterior` e `mensagens_commits`), como no CFR (b).
    """
    n_corretivas = sum(1 for r in classificar_releases(releases) if r["corretiva"])
    return {
        "rework_rate": n_corretivas / len(releases) if releases else None,
        "n_releases_corretivas": n_corretivas,
    }


def avaliar_heuristica(rotulos_heuristica: list[bool], rotulos_consenso: list[bool]) -> dict:
    """Precisao, recall e F1 da heuristica de release corretiva frente ao consenso.

    `rotulos_heuristica` e `rotulos_consenso` devem estar alinhados pela mesma
    ordem de releases (saida da amostra-ouro validada manualmente, secao 6).
    """
    if len(rotulos_heuristica) != len(rotulos_consenso):
        raise ValueError("rotulos_heuristica e rotulos_consenso devem ter o mesmo tamanho")

    verdadeiros_positivos = sum(
        1 for h, c in zip(rotulos_heuristica, rotulos_consenso) if h and c
    )
    falsos_positivos = sum(
        1 for h, c in zip(rotulos_heuristica, rotulos_consenso) if h and not c
    )
    falsos_negativos = sum(
        1 for h, c in zip(rotulos_heuristica, rotulos_consenso) if not h and c
    )

    precisao = (
        verdadeiros_positivos / (verdadeiros_positivos + falsos_positivos)
        if (verdadeiros_positivos + falsos_positivos)
        else None
    )
    recall = (
        verdadeiros_positivos / (verdadeiros_positivos + falsos_negativos)
        if (verdadeiros_positivos + falsos_negativos)
        else None
    )
    f1 = (
        2 * precisao * recall / (precisao + recall)
        if precisao is not None and recall is not None and (precisao + recall) > 0
        else None
    )

    return {"precisao": precisao, "recall": recall, "f1": f1}
