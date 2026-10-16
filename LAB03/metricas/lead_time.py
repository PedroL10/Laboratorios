"""Calculo do lead time for changes (RQ 02), nas duas variantes obrigatorias.

Cada release e representada por um dicionario:

    {
        "tag_name": "v1.1",
        "published_at": "2024-03-15T00:00:00Z",
        "commits": ["2024-03-02T00:00:00Z", "2024-03-10T00:00:00Z", ...],
    }

`commits` traz a data de autor (`commit.author.date`) de cada commit incluido na
release, obtida comparando-a com a release anterior. Releases sem release
anterior (a primeira da historia do repositorio) nao entram aqui: quem monta a
lista (`pipeline.commits`) ja as deixa de fora.

- **Variante (a), por release:** `lead_time_por_release` devolve um unico valor
  por release, a partir do commit mais antigo nela incluido.
- **Variante (b), por commit:** `lead_times_por_commit` devolve um valor por
  commit da release; todos os commits de todas as releases entram na mediana
  do repositorio.
"""

from __future__ import annotations

import statistics
from datetime import datetime


def _parse(data_iso: str) -> datetime:
    return datetime.fromisoformat(data_iso.replace("Z", "+00:00"))


def lead_time_dias(data_fim: datetime, data_inicio: datetime) -> float:
    """Diferenca entre duas datas, em dias (pode ter fracao)."""
    return (data_fim - data_inicio).total_seconds() / 86400


def lead_time_por_release(release: dict) -> float | None:
    """Variante (a): dias entre a release e o commit mais antigo nela incluido.

    Devolve None se a release nao tem commits novos (ex.: release republicada
    sem mudancas), caso de borda que deve ser contado como ausencia de dado,
    nao como lead time zero.
    """
    commits = release.get("commits") or []
    if not commits:
        return None
    publicada_em = _parse(release["published_at"])
    mais_antigo = min(_parse(c) for c in commits)
    return lead_time_dias(publicada_em, mais_antigo)


def lead_times_por_commit(release: dict) -> list[float]:
    """Variante (b): um lead time por commit incluido na release."""
    commits = release.get("commits") or []
    if not commits:
        return []
    publicada_em = _parse(release["published_at"])
    return [lead_time_dias(publicada_em, _parse(c)) for c in commits]


def mediana(valores: list[float]) -> float | None:
    """Mediana de uma lista, ou None se a lista estiver vazia (sem dado)."""
    return statistics.median(valores) if valores else None


def lead_time_repositorio(releases: list[dict]) -> dict:
    """Agrega as duas variantes de lead time para um repositorio.

    `releases` deve conter apenas releases que tem release anterior (a
    primeira release da historia ja vem excluida por quem monta a lista).
    Releases sem commits novos nao entram na variante (a), mas nao impedem o
    calculo das demais.
    """
    valores_a = [v for r in releases for v in [lead_time_por_release(r)] if v is not None]
    valores_b = [v for r in releases for v in lead_times_por_commit(r)]
    return {
        "lead_time_release_dias": mediana(valores_a),
        "lead_time_commit_dias": mediana(valores_b),
        "n_releases_variante_a": len(valores_a),
        "n_commits_variante_b": len(valores_b),
    }
