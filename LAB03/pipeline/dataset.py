"""Dataset final (`resultados/amostra_metricas.csv`) e dicionario de dados.

Junta, por `full_name`, a amostra com metadados (`resultados/amostra.csv`) e os
CSVs de metricas que o pipeline grava em `dados/` (frequencia, lead time, CFR
nas duas variantes, tempo de recuperacao e variantes da RQ 07), e acrescenta a
classificacao DORA de referencia (C1: release, lead time a, CFR a). Uma linha
por repositorio, na ordem da amostra. Valor ausente fica vazio.

Esta etapa nao chama a API: pode ser refeita a qualquer momento, sem token,
com `python -m pipeline.dataset --config config.yaml`.

O dicionario de dados (`DICIONARIO`) documenta cada coluna com tipo, unidade e
formula ou origem na API, e e gravado em `resultados/dicionario_dados.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from metricas.classificacao import classificar_repositorio
from pipeline.config import load_config
from pipeline.selecao import carregar_csv, salvar_csv

# Arquivos de metricas em `dados_dir`, na ordem em que as colunas entram no dataset.
# Uma coluna repetida (n_releases_janela, que tambem esta na amostra) fica com o
# valor do arquivo mais a direita.
ARQUIVOS_METRICAS = [
    "frequencia.csv",
    "lead_time.csv",
    "cfr.csv",
    "cfr_ci.csv",
    "recuperacao.csv",
    "variantes.csv",
]

_VARIANTES = {
    "pre": "release + pre-release (toda release que nao e draft)",
    "tag": "tag (data = committedDate do commit apontado, via GraphQL)",
}

# (coluna, tipo, unidade, descricao: formula ou origem na API)
DICIONARIO: list[tuple[str, str, str, str]] = [
    # Identificacao e metadados (etapas 1 a 5)
    ("full_name", "texto", "-", "`owner/nome` do repositorio (`full_name` da busca)"),
    ("owner", "texto", "-", "Dono do repositorio (`owner.login`)"),
    ("name", "texto", "-", "Nome do repositorio (`name`)"),
    ("stargazers_count", "inteiro", "estrelas", "Estrelas no momento da busca (`stargazers_count`)"),
    ("language", "texto", "-", "Linguagem principal segundo o GitHub (`language`); vazio se nao detectada"),
    ("created_at", "data-hora ISO 8601 (UTC)", "-", "Criacao do repositorio (`created_at`)"),
    ("default_branch", "texto", "-", "Branch principal (`default_branch`); o unico considerado"),
    ("archived", "booleano", "-", "Repositorio arquivado (`archived`)"),
    ("fork", "booleano", "-", "Repositorio e fork (`fork`)"),
    ("html_url", "texto", "-", "Endereco do repositorio no GitHub (`html_url`)"),
    ("n_runs_push", "inteiro", "runs", "`total_count` de `actions/runs?event=push&branch=<default>&created=<janela>` (criterio de inclusao)"),
    ("n_runs_validos", "inteiro", "runs", "Runs de push com `conclusion` de sucesso ou falha na janela (criterio de inclusao); limite inferior se `runs_no_teto`"),
    ("runs_no_teto", "booleano", "-", "`n_runs_push` atingiu o teto de 2.500 do `total_count` da API (contagens do criterio sao limites inferiores)"),
    ("n_contribuidores", "inteiro", "pessoas", "Contribuidores, inclusive anonimos: ultima pagina de `contributors?per_page=1&anon=true`"),
    ("erro_contribuidores", "texto", "-", "Motivo de `n_contribuidores` vazio (ex.: lista grande demais para a API); vazio se contou"),
    ("idade_dias", "inteiro", "dias", "Fim da janela - `created_at`"),
    # RQ 01
    ("deployment_frequency", "decimal", "releases/semana", "RQ 01: `n_releases_janela / semanas_janela`"),
    ("n_releases_janela", "inteiro", "releases", "Releases publicadas (`draft = false`, `prerelease = false`) com `published_at` na janela"),
    ("semanas_janela", "decimal", "semanas", "Dias da janela (inclusive) / 7 = 52,14"),
    # RQ 02
    ("lead_time_release_dias", "decimal", "dias", "RQ 02 (a): mediana, entre as releases da janela, de `published_at` - `commit.author.date` do commit mais antigo da release (`compare/<anterior>...<release>`)"),
    ("lead_time_commit_dias", "decimal", "dias", "RQ 02 (b): mediana de `published_at` - `commit.author.date` de todos os commits de todas as releases da janela"),
    ("n_releases_variante_a", "inteiro", "releases", "Releases com ao menos um commit novo, usadas na variante (a)"),
    ("n_commits_variante_b", "inteiro", "commits", "Commits usados na variante (b)"),
    ("n_ignoradas_primeira_release", "inteiro", "releases", "1 se a primeira release da historia do repositorio esta na janela (sem release anterior para comparar); 0 caso contrario"),
    ("n_ignoradas_compare_404", "inteiro", "releases", "Releases da janela ignoradas porque o `compare` devolveu 404 (tag apagada ou reescrita)"),
    # RQ 03
    ("cfr_entrega", "proporcao (0 a 1)", "-", "RQ 03 (b): `n_releases_falhas / n_releases_avaliadas`; release falha se a seguinte, em ate 7 dias, e corretiva pela heuristica (`metricas.cfr`)"),
    ("n_releases_avaliadas", "inteiro", "releases", "Releases da janela avaliadas no CFR (b) (exclui as censuradas)"),
    ("n_releases_falhas", "inteiro", "releases", "Releases seguidas, em ate 7 dias, por uma release corretiva"),
    ("n_releases_censuradas", "inteiro", "releases", "Releases publicadas nos ultimos 7 dias da janela, fora do denominador do CFR (b)"),
    ("cfr_ci", "proporcao (0 a 1)", "-", "RQ 03 (a): `n_runs_falha / (n_runs_falha + n_runs_sucesso)`, runs de push no default branch na janela"),
    ("n_runs_falha", "inteiro", "runs", "Runs com `conclusion` em failure, timed_out ou startup_failure"),
    ("n_runs_sucesso", "inteiro", "runs", "Runs com `conclusion` = success"),
    ("n_runs_ignorados", "inteiro", "runs", "Runs com outro `conclusion` (cancelled, skipped, neutral, action_required, stale ou vazio)"),
    ("fatias_no_teto", "inteiro", "dias", "Dias com mais de 1.000 runs (teto de uma consulta filtrada): runs desses dias estao incompletos"),
    # RQ 04
    ("tempo_recuperacao_horas", "decimal", "horas", "RQ 04: mediana dos episodios de todos os workflows; episodio = `updated_at` do sucesso - `run_started_at` da primeira falha apos um sucesso, no mesmo `workflow_id`"),
    ("n_episodios", "inteiro", "episodios", "Episodios de falha encerrados na janela"),
    ("n_episodios_censurados", "inteiro", "episodios", "Episodios sem sucesso ate o fim da janela (fora da mediana)"),
    ("proporcao_censurados", "proporcao (0 a 1)", "-", "`n_episodios_censurados / (n_episodios + n_episodios_censurados)`"),
    ("n_episodios_sem_inicio", "inteiro", "workflows", "Workflows que ja comecam a janela falhando (inicio do episodio desconhecido; fora da mediana)"),
] + [
    (f"{coluna}_{sufixo}", tipo, unidade, f"{descricao}, com unidade de deploy = {_VARIANTES[sufixo]} (RQ 07)")
    for sufixo in _VARIANTES
    for coluna, tipo, unidade, descricao in [
        ("deployment_frequency", "decimal", "unidades/semana", "Frequencia de deploy"),
        ("n_unidades_janela", "inteiro", "unidades", "Unidades de deploy com data na janela"),
        ("lead_time_release_dias", "decimal", "dias", "Lead time (a), por unidade"),
        ("lead_time_commit_dias", "decimal", "dias", "Lead time (b), por commit"),
        ("cfr_entrega", "proporcao (0 a 1)", "-", "CFR (b)"),
        ("n_avaliadas_cfr", "inteiro", "unidades", "Unidades avaliadas no CFR (b)"),
    ]
] + [
    # Classificacao DORA de referencia (C1)
    ("categoria_frequencia", "categoria", "-", "Elite/High/Medium/Low de `deployment_frequency` (cortes da RQ 07, `metricas.classificacao`)"),
    ("categoria_lead_time", "categoria", "-", "Elite/High/Medium/Low de `lead_time_release_dias` (variante a)"),
    ("categoria_cfr", "categoria", "-", "Elite/High/Medium/Low de `cfr_ci` (variante a)"),
    ("categoria_recuperacao", "categoria", "-", "Elite/High/Medium/Low de `tempo_recuperacao_horas`"),
    ("categoria_geral", "categoria", "-", "Combinacao C1: mediana dos pontos (Elite 4 ... Low 1) das metricas disponiveis, arredondada para baixo"),
    ("n_metricas", "inteiro", "metricas", "Quantas das 4 metricas tem valor e entraram em `categoria_geral`"),
]

COLUNAS = [coluna for coluna, *_ in DICIONARIO]


def _float_ou_none(valor) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def classificacao_c1(linha: dict) -> dict:
    """Classificacao DORA de referencia (C1): release, lead time (a) e CFR (a)."""
    return classificar_repositorio(
        _float_ou_none(linha.get("deployment_frequency")),
        _float_ou_none(linha.get("lead_time_release_dias")),
        _float_ou_none(linha.get("cfr_ci")),
        _float_ou_none(linha.get("tempo_recuperacao_horas")),
    )


def montar_dataset(amostra: list[dict], tabelas: list[list[dict]]) -> list[dict]:
    """Junta a amostra e as tabelas de metricas por `full_name`, uma linha por repositorio."""
    indices = [{linha["full_name"]: linha for linha in tabela} for tabela in tabelas]
    dataset = []
    for repo in amostra:
        linha = dict(repo)
        for indice in indices:
            linha.update(indice.get(repo["full_name"], {}))
        linha.update(classificacao_c1(linha))
        dataset.append({coluna: linha.get(coluna, "") for coluna in COLUNAS})
    return dataset


def dicionario_markdown() -> str:
    linhas = [
        "# Dicionario de dados — `resultados/amostra_metricas.csv`",
        "",
        "Uma linha por repositorio da amostra. Gerado por `pipeline/dataset.py`, a partir",
        "de `DICIONARIO`. Valor vazio = metrica sem dado para o repositorio (ex.: nenhum",
        "episodio de falha encerrado na janela). Datas em UTC. A janela de observacao e a",
        "do `config.yaml`, com inicio e fim inclusivos.",
        "",
        "| Coluna | Tipo | Unidade | Formula / origem |",
        "| --- | --- | --- | --- |",
    ]
    linhas += [f"| `{c}` | {t} | {u} | {d} |" for c, t, u, d in DICIONARIO]
    return "\n".join(linhas) + "\n"


def gerar_dataset(dados_dir: Path, resultados_dir: Path) -> list[dict]:
    """Le os CSVs, grava o dataset e o dicionario em `resultados_dir` e devolve o dataset."""
    amostra = carregar_csv(resultados_dir / "amostra.csv")
    tabelas = []
    for nome in ARQUIVOS_METRICAS:
        caminho = dados_dir / nome
        if not caminho.exists():
            print(f"    AVISO: {caminho} nao existe; as colunas dele ficam vazias.")
            continue
        tabelas.append(carregar_csv(caminho))

    dataset = montar_dataset(amostra, tabelas)
    salvar_csv(dataset, resultados_dir / "amostra_metricas.csv", COLUNAS)
    (resultados_dir / "dicionario_dados.md").write_text(dicionario_markdown(), encoding="utf-8")
    return dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pipeline.dataset", description="Monta o dataset final a partir dos CSVs ja coletados."
    )
    parser.add_argument("--config", default="config.yaml", help="Caminho do config.yaml")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    dados_dir = Path(config.get("dados_dir", "dados"))
    resultados_dir = Path(config.get("resultados_dir", "resultados"))

    dataset = gerar_dataset(dados_dir, resultados_dir)
    print(
        f"Dataset de {len(dataset)} repositorios salvo em {resultados_dir / 'amostra_metricas.csv'}; "
        f"dicionario em {resultados_dir / 'dicionario_dados.md'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
