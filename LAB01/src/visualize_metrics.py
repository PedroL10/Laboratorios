"""Gera os graficos das RQs da Sprint 3.

Uso:
    python src/analyze_metrics.py                 # gera resultados/resultados_metricas_1000.json
    python src/visualize_metrics.py                # gera os PNGs a partir desse JSON

Cada grafico corresponde a uma Questao de Pesquisa e usa um tipo adequado ao
dado: distribuicoes para releases/atualizacao, ranking para linguagem, barra
100% para issues fechadas e comparacoes por linguagem/grupo para RQ07 e RQ08.
"""

import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "resultados", "resultados_metricas_1000.json")
REPOS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "repositorios_lab01_s02.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "resultados", "graficos")

COR_PRINCIPAL = "#2E5266"
COR_DESTAQUE = "#6CC24A"


def _save(fig, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Grafico salvo em {path}")


def _load_repos(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def plot_rq01_idade(repos, reference_at):
    idades_anos = [
        (reference_at - datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days / 365
        for r in repos
    ]
    mediana = statistics.median(idades_anos)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(idades_anos, bins=20, color=COR_PRINCIPAL)
    ax.axvline(mediana, color=COR_DESTAQUE, linestyle="--", label=f"Mediana: {mediana:.1f} anos")
    ax.set_title("RQ01 - Sistemas populares sao maduros/antigos?")
    ax.set_xlabel("Idade do repositorio (anos)")
    ax.set_ylabel("Quantidade de repositorios")
    ax.legend()
    _save(fig, "rq01_idade.png")


def plot_rq02_prs(repos):
    prs = [int(r["pull_requests_merged_total"]) for r in repos]
    sem_prs = sum(1 for p in prs if p == 0)
    prs_positivos = [p for p in prs if p > 0]
    mediana = statistics.median(prs)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(prs_positivos, bins=30, color=COR_PRINCIPAL)
    ax.set_xscale("log")
    ax.axvline(mediana, color=COR_DESTAQUE, linestyle="--", label=f"Mediana: {mediana:.0f} PRs")
    ax.set_title("RQ02 - Sistemas populares recebem muita contribuicao externa?")
    ax.set_xlabel("Pull requests aceitas (escala log)")
    ax.set_ylabel("Quantidade de repositorios")
    ax.legend(title=f"{sem_prs} repositorios com 0 PRs aceitas nao\nentram no histograma (escala log)")
    _save(fig, "rq02_prs_aceitas.png")


def plot_rq07_por_linguagem(metrics, min_repos=10):
    por_lang = dict(_grupos_rq07(metrics, min_repos))

    fig, ax = plt.subplots(figsize=(9, 6))
    for i, (lang, dados) in enumerate(por_lang.items()):
        ax.scatter(
            dados["mediana_releases"],
            dados["mediana_prs_aceitas"],
            s=dados["quantidade_repos"] * 2,
            color=COR_PRINCIPAL,
            alpha=0.7,
        )
        offset_y = 10 if i % 2 == 0 else -14
        ax.annotate(lang, (dados["mediana_releases"], dados["mediana_prs_aceitas"]), fontsize=8,
                    xytext=(6, offset_y), textcoords="offset points")

    ax.set_title("RQ07 - Releases vs. PRs aceitas, por linguagem (mediana)")
    ax.set_xlabel("Mediana de releases")
    ax.set_ylabel("Mediana de PRs aceitas")
    _save(fig, "rq07_releases_vs_prs.png")


def plot_rq03_releases(metrics):
    repos = _load_repos(REPOS_PATH)
    releases = [int(r["releases_total"]) for r in repos]
    categorias = {
        "0": sum(value == 0 for value in releases),
        "1–9": sum(1 <= value <= 9 for value in releases),
        "10–49": sum(10 <= value <= 49 for value in releases),
        "50–99": sum(50 <= value <= 99 for value in releases),
        "100+": sum(value >= 100 for value in releases),
    }
    mediana = metrics["RQ03_releases"]["mediana"]

    fig, ax = plt.subplots(figsize=(6, 4))
    barras = ax.bar(categorias.keys(), categorias.values(), color=COR_PRINCIPAL)
    barras[0].set_color(COR_DESTAQUE)
    ax.set_title("RQ03 - Distribuicao de releases por repositorio")
    ax.set_xlabel("Faixa de releases publicadas")
    ax.set_ylabel("Quantidade de repositorios")
    ax.text(
        0.98,
        0.95,
        f"Mediana: {mediana:.0f} releases",
        ha="right",
        va="top",
        transform=ax.transAxes,
    )
    for i, value in enumerate(categorias.values()):
        ax.text(i, value, str(value), ha="center", va="bottom")
    _save(fig, "rq03_releases.png")


def plot_rq04_atualizacao(metrics):
    repos = _load_repos(REPOS_PATH)
    reference_at = datetime.fromisoformat(
        metrics["analysis_reference_at"].replace("Z", "+00:00")
    )
    dias_sem_update = [
        (reference_at - datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days
        for r in repos
    ]
    mediana = metrics["RQ04_atualizacao"]["mediana_dias"]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(dias_sem_update, bins=30, color=COR_PRINCIPAL)
    ax.set_xscale("log")
    ax.axvline(mediana, color=COR_DESTAQUE, linestyle="--", label=f"Mediana: {mediana:.0f} dias")
    ax.set_title("RQ04 - Tempo desde o ultimo push")
    ax.set_xlabel("Dias desde o ultimo push (escala log)")
    ax.set_ylabel("Quantidade de repositorios")
    ax.legend()
    _save(fig, "rq04_atualizacao.png")


def plot_rq05_linguagem(metrics):
    distribuicao = metrics["RQ05_linguagem"]["distribuicao_top10"]
    linguagens = [d["linguagem"] for d in distribuicao][::-1]
    quantidades = [d["quantidade"] for d in distribuicao][::-1]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(linguagens, quantidades, color=COR_PRINCIPAL)
    ax.set_title("RQ05 - Linguagens primarias mais usadas (top 10)")
    ax.set_xlabel("Quantidade de repositorios")
    for i, v in enumerate(quantidades):
        ax.text(v, i, f" {v}", va="center")
    _save(fig, "rq05_linguagem.png")


def plot_rq06_issues_fechadas(metrics):
    rq06 = metrics["RQ06_issues_fechadas"]
    mediana = rq06["mediana_percentual"]

    fig, ax = plt.subplots(figsize=(6, 2.5))
    ax.barh(["% issues fechadas"], [100], color="#DDDDDD")
    ax.barh(["% issues fechadas"], [mediana], color=COR_DESTAQUE)
    ax.set_xlim(0, 100)
    ax.set_title("RQ06 - Sistemas populares possuem alto % de issues fechadas?")
    ax.set_xlabel("Percentual de issues fechadas (mediana por repositorio)")
    ax.text(mediana, 0, f" {mediana}%", va="center")
    _save(fig, "rq06_issues_fechadas.png")


def _grupos_rq07(metrics, min_repos=10):
    return [
        (linguagem, dados)
        for linguagem, dados in metrics["RQ07_por_linguagem"].items()
        if linguagem != "Nao informado" and dados["quantidade_repos"] >= min_repos
    ]


def plot_rq07_atualizacao_por_linguagem(metrics):
    """Completa RQ07 com a terceira metrica: atualizacao por linguagem."""
    grupos = _grupos_rq07(metrics)
    grupos.sort(key=lambda item: item[1]["mediana_dias_sem_update"], reverse=True)
    linguagens = [f"{linguagem} (n={dados['quantidade_repos']})" for linguagem, dados in grupos]
    valores = [dados["mediana_dias_sem_update"] for _, dados in grupos]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(linguagens, valores, color=COR_PRINCIPAL)
    ax.set_title("RQ07 - Atualizacao por linguagem primaria")
    ax.set_xlabel("Mediana de dias desde o ultimo push")
    ax.set_ylabel("Linguagem primaria (n de repositorios)")
    for i, value in enumerate(valores):
        ax.text(value, i, f" {value:g}", va="center")
    _save(fig, "rq07_atualizacao_por_linguagem.png")


def plot_rq08_sem_linguagem(metrics):
    """Mostra a comparacao exploratoria entre grupos da RQ08."""
    rq08 = metrics["RQ08_sem_linguagem"]
    grupos = [rq08["com_linguagem"], rq08["sem_linguagem"]]
    rotulos = [
        f"Com linguagem\n(n={grupos[0]['quantidade_repos']})",
        f"Sem linguagem\n(n={grupos[1]['quantidade_repos']})",
    ]
    metricas = [
        ("mediana_prs_aceitas", "PRs aceitas", COR_PRINCIPAL),
        ("mediana_releases", "Releases", COR_DESTAQUE),
        ("mediana_dias_sem_update", "Dias sem push", "#D17842"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    for ax, (chave, titulo, cor) in zip(axes, metricas):
        valores = [grupo[chave] for grupo in grupos]
        ax.bar(rotulos, valores, color=cor)
        ax.set_title(titulo)
        ax.set_ylabel("Mediana por repositorio")
        for i, value in enumerate(valores):
            ax.text(i, value, f"{value:g}", ha="center", va="bottom")
    fig.suptitle("RQ08 - Indicadores por presenca de linguagem primaria", y=1.02)
    _save(fig, "rq08_sem_linguagem.png")


def main(metrics_path, repos_path):
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)
    repos = _load_repos(repos_path)
    reference_at = datetime.fromisoformat(
        metrics["analysis_reference_at"].replace("Z", "+00:00")
    )

    plot_rq01_idade(repos, reference_at)
    plot_rq02_prs(repos)
    plot_rq03_releases(metrics)
    plot_rq04_atualizacao(metrics)
    plot_rq05_linguagem(metrics)
    plot_rq06_issues_fechadas(metrics)
    plot_rq07_por_linguagem(metrics)
    plot_rq07_atualizacao_por_linguagem(metrics)
    plot_rq08_sem_linguagem(metrics)


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else METRICS_PATH,
        sys.argv[2] if len(sys.argv) > 2 else REPOS_PATH,
    )
