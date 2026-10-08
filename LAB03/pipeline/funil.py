"""Funil de selecao: quantos repositorios restaram em cada etapa e por que os demais sairam.

A tabela e montada a partir dos resultados das etapas anteriores (nenhuma chamada
a API) e vai para a secao de Metodologia do artigo (secao 7 do enunciado).

Etapas:
1. candidatos da busca por faixas de estrelas;
2. candidatos que usam GitHub Actions;
3. avaliados pelo criterio de inclusao (em ordem de estrelas, ate completar a amostra);
4. com o minimo de releases na janela;
5. com o minimo de runs validos na janela (amostra final).
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from pipeline.criterio_inclusao import incluido
from pipeline.filtro_actions import usa_actions

FUNIL_FIELDS = ["etapa", "descricao", "repositorios", "descartados", "motivos_descarte"]

AMOSTRA_FIELDS_CRITERIO = ["n_releases_janela", "n_runs_push", "n_runs_validos", "runs_no_teto"]

MOTIVO_NAO_AVALIADO = "nao_avaliado_amostra_completa"


def _etapa(
    numero: int, descricao: str, repositorios: int, anterior: int | None, motivos: Counter
) -> dict:
    return {
        "etapa": numero,
        "descricao": descricao,
        "repositorios": repositorios,
        "descartados": 0 if anterior is None else anterior - repositorios,
        "motivos_descarte": dict(sorted(motivos.items())),
    }


def _falhou_nas_releases(linha: dict) -> bool:
    """Descartado antes de contar runs: poucas releases ou erro ao lista-las."""
    return linha["n_runs_push"] in (None, "") and not incluido(linha)


def montar_funil(
    candidatos: list[dict],
    filtro_actions: list[dict],
    avaliados: list[dict],
    estrelas_min: int,
    min_releases: int,
    min_runs: int,
) -> list[dict]:
    """Monta as linhas do funil (`motivos_descarte` e um dict motivo -> quantidade).

    `filtro_actions` tem uma linha por candidato; `avaliados` tem as linhas do
    criterio de inclusao dos repositorios que chegaram a ser avaliados.
    """
    com_actions = [f for f in filtro_actions if usa_actions(f)]
    motivos_actions = Counter(f["motivo_descarte"] for f in filtro_actions if not usa_actions(f))

    nao_avaliados = len(com_actions) - len(avaliados)
    motivos_avaliacao = Counter({MOTIVO_NAO_AVALIADO: nao_avaliados} if nao_avaliados else {})

    descartados_releases = [a for a in avaliados if _falhou_nas_releases(a)]
    descartados_runs = [a for a in avaliados if not incluido(a) and not _falhou_nas_releases(a)]
    n_com_releases = len(avaliados) - len(descartados_releases)
    n_amostra = sum(map(incluido, avaliados))

    return [
        _etapa(
            1,
            f"Candidatos da busca (stars:>{estrelas_min}, mais estrelados primeiro)",
            len(candidatos),
            None,
            Counter(),
        ),
        _etapa(2, "Usam GitHub Actions", len(com_actions), len(candidatos), motivos_actions),
        _etapa(
            3,
            "Avaliados pelo criterio de inclusao",
            len(avaliados),
            len(com_actions),
            motivos_avaliacao,
        ),
        _etapa(
            4,
            f">= {min_releases} releases na janela",
            n_com_releases,
            len(avaliados),
            Counter(a["motivo_descarte"] for a in descartados_releases),
        ),
        _etapa(
            5,
            f">= {min_runs} runs validos na janela (amostra final)",
            n_amostra,
            n_com_releases,
            Counter(a["motivo_descarte"] for a in descartados_runs),
        ),
    ]


def funil_para_csv(funil: list[dict]) -> list[dict]:
    """Converte os motivos de cada etapa em texto ("motivo: n; ...") para o CSV."""
    return [
        {
            **etapa,
            "motivos_descarte": "; ".join(
                f"{m}: {n}" for m, n in etapa["motivos_descarte"].items()
            ),
        }
        for etapa in funil
    ]


def montar_amostra(candidatos: list[dict], avaliados: list[dict]) -> list[dict]:
    """Junta os metadados da busca com as contagens do criterio para os incluidos."""
    por_nome = {c["full_name"]: c for c in candidatos}
    amostra = []
    for linha in avaliados:
        if incluido(linha):
            repo = dict(por_nome[linha["full_name"]])
            repo.update({campo: linha[campo] for campo in AMOSTRA_FIELDS_CRITERIO})
            amostra.append(repo)
    return amostra


def descrever_motivo(motivo: str) -> str:
    """Traduz o codigo do motivo de descarte para texto legivel."""
    if motivo == "sem_workflows":
        return "sem workflows do GitHub Actions"
    if motivo == MOTIVO_NAO_AVALIADO:
        return "nao avaliados (amostra ja completa)"
    if m := re.fullmatch(r"menos_de_(\d+)_releases", motivo):
        return f"menos de {m[1]} releases na janela"
    if m := re.fullmatch(r"menos_de_(\d+)_runs_validos", motivo):
        return f"menos de {m[1]} runs validos na janela"
    if m := re.fullmatch(r"erro_http_(\w+)", motivo):
        return f"erro HTTP {m[1]}"
    return motivo


def funil_markdown(funil: list[dict], janela: str) -> str:
    """Gera a tabela do funil em Markdown, pronta para o artigo e para a Issue."""
    linhas = [
        "# Funil de selecao",
        "",
        f"Janela de observacao: {janela}",
        "",
        "| Etapa | Descricao | Repositorios | Descartados | Motivo do descarte |",
        "| ----: | --------- | -----------: | ----------: | ------------------ |",
    ]
    for etapa in funil:
        motivos = "; ".join(
            f"{descrever_motivo(m)}: {n}" for m, n in etapa["motivos_descarte"].items()
        )
        linhas.append(
            f"| {etapa['etapa']} | {etapa['descricao']} | {etapa['repositorios']} "
            f"| {etapa['descartados'] or '-'} | {motivos or '-'} |"
        )
    resumo = " -> ".join(str(e["repositorios"]) for e in funil)
    linhas += ["", f"Resumo: {resumo}", ""]
    return "\n".join(linhas)


def salvar_markdown(texto: str, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")
    return caminho
