"""
Lab01S03 - Sprint 3: Análise, visualização e relatório final.

Lê os dados coletados na Sprint 2 (CSV), calcula estatísticas para responder
as RQs, gera gráficos e escreve o relatório final em Markdown.
"""

import csv
import os
import math
import statistics
from collections import Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "docs", "Sprint2", "repositorios.csv")
SPRINT3_DIR = os.path.join(BASE_DIR, "docs", "Sprint3")
FIGURES_DIR = os.path.join(SPRINT3_DIR, "figures")
REPORT_PATH = os.path.join(SPRINT3_DIR, "Relatorio_Final_Sprint3.md")


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_data(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")

    rows = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalizações para análise
            row["estrelas"] = to_int(row.get("estrelas"))
            row["prs_merged"] = to_int(row.get("prs_merged"))
            row["releases"] = to_int(row.get("releases"))
            row["issues_total"] = to_int(row.get("issues_total"))
            row["issues_fechadas"] = to_int(row.get("issues_fechadas"))
            row["idade_dias"] = to_int(row.get("idade_dias"))
            row["dias_desde_atualizacao"] = max(0, to_int(row.get("dias_desde_atualizacao")))
            row["razao_issues_fechadas"] = to_float(row.get("razao_issues_fechadas"), default=0.0)
            row["linguagem"] = (row.get("linguagem") or "Não especificada").strip() or "Não especificada"
            rows.append(row)

    return rows


def median(values):
    clean = [v for v in values if v is not None]
    return statistics.median(clean) if clean else 0


def mean(values):
    clean = [v for v in values if v is not None]
    return statistics.mean(clean) if clean else 0


def compute_metrics(rows):
    total = len(rows)
    estrelas = [r["estrelas"] for r in rows]
    prs = [r["prs_merged"] for r in rows]
    releases = [r["releases"] for r in rows]
    idade_dias = [r["idade_dias"] for r in rows]
    idade_anos = [r["idade_dias"] / 365 for r in rows]
    dias_atualizacao = [r["dias_desde_atualizacao"] for r in rows]
    razoes = [r["razao_issues_fechadas"] for r in rows if r["issues_total"] > 0]

    linguagens = Counter(r["linguagem"] for r in rows)
    top10_linguagens = linguagens.most_common(10)

    metrics = {
        "total_repos": total,
        "estrelas_max": max(estrelas) if estrelas else 0,
        "estrelas_min": min(estrelas) if estrelas else 0,
        "estrelas_media": mean(estrelas),
        "idade_mediana_dias": median(idade_dias),
        "idade_mediana_anos": median(idade_anos),
        "idade_media_anos": mean(idade_anos),
        "prs_mediana": median(prs),
        "prs_media": mean(prs),
        "releases_mediana": median(releases),
        "releases_media": mean(releases),
        "dias_desde_update_mediana": median(dias_atualizacao),
        "dias_desde_update_media": mean(dias_atualizacao),
        "issues_ratio_mediana": median(razoes),
        "issues_ratio_media": mean(razoes),
        "top10_linguagens": top10_linguagens,
        "linguagens_counter": linguagens,
        "raw": {
            "idade_anos": idade_anos,
            "prs": prs,
            "releases": releases,
            "dias_atualizacao": dias_atualizacao,
            "razoes": razoes,
        },
    }

    return metrics


def evaluate_hypotheses(metrics):
    """
    Regras objetivas para suportar decisão no relatório.
    """
    h = {}

    # H1: maduros/antigos -> mediana >= 5 anos
    h["RQ01"] = (metrics["idade_mediana_anos"] >= 5, f"Mediana de idade = {metrics['idade_mediana_anos']:.2f} anos")

    # H2: muita contribuição externa -> mediana de PRs >= 100
    h["RQ02"] = (metrics["prs_mediana"] >= 100, f"Mediana de PRs merged = {metrics['prs_mediana']:.0f}")

    # H3: releases frequentes -> mediana de releases >= 10
    h["RQ03"] = (metrics["releases_mediana"] >= 10, f"Mediana de releases = {metrics['releases_mediana']:.0f}")

    # H4: atualizados com frequência -> mediana <= 30 dias
    h["RQ04"] = (metrics["dias_desde_update_mediana"] <= 30, f"Mediana desde última atualização = {metrics['dias_desde_update_mediana']:.0f} dias")

    # H5: linguagens populares -> presença de JS/Python/Java/TS no topo
    top_langs = [name for name, _ in metrics["top10_linguagens"]]
    populares = {"JavaScript", "Python", "Java", "TypeScript"}
    inter = populares.intersection(set(top_langs[:10]))
    h["RQ05"] = (len(inter) >= 3, f"Top linguagens contém {', '.join(sorted(inter)) if inter else 'nenhuma linguagem esperada'}")

    # H6: alto percentual de issues fechadas -> mediana >= 80%
    h["RQ06"] = (metrics["issues_ratio_mediana"] >= 0.80, f"Mediana da razão de issues fechadas = {metrics['issues_ratio_mediana']:.2%}")

    return h


def _safe_import_matplotlib():
    try:
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None


def generate_charts(metrics):
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt = _safe_import_matplotlib()
    if plt is None:
        print("[Aviso] matplotlib não está instalado. Gráficos não foram gerados.")
        return []

    generated = []

    # 1) Top linguagens
    langs, counts = zip(*metrics["top10_linguagens"]) if metrics["top10_linguagens"] else ([], [])
    fig = plt.figure(figsize=(10, 5))
    plt.bar(langs, counts)
    plt.xticks(rotation=30, ha="right")
    plt.title("Top 10 linguagens (1000 repositórios)")
    plt.tight_layout()
    p1 = os.path.join(FIGURES_DIR, "top_linguagens.png")
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    generated.append(p1)

    # 2) Distribuição da idade (anos)
    fig = plt.figure(figsize=(10, 5))
    plt.hist(metrics["raw"]["idade_anos"], bins=30)
    plt.title("Distribuição da idade dos repositórios (anos)")
    plt.xlabel("Idade (anos)")
    plt.ylabel("Quantidade")
    plt.tight_layout()
    p2 = os.path.join(FIGURES_DIR, "distribuicao_idade.png")
    fig.savefig(p2, dpi=150)
    plt.close(fig)
    generated.append(p2)

    # 3) Distribuição da razão de issues fechadas
    fig = plt.figure(figsize=(10, 5))
    plt.hist(metrics["raw"]["razoes"], bins=25)
    plt.title("Distribuição da razão de issues fechadas")
    plt.xlabel("Razão (0 a 1)")
    plt.ylabel("Quantidade")
    plt.tight_layout()
    p3 = os.path.join(FIGURES_DIR, "distribuicao_issues_fechadas.png")
    fig.savefig(p3, dpi=150)
    plt.close(fig)
    generated.append(p3)

    # 4) Boxplot de PRs merged
    fig = plt.figure(figsize=(8, 5))
    plt.boxplot(metrics["raw"]["prs"], vert=True)
    plt.yscale("symlog")
    plt.title("Boxplot de PRs merged (escala log)")
    plt.ylabel("PRs merged")
    plt.tight_layout()
    p4 = os.path.join(FIGURES_DIR, "boxplot_prs.png")
    fig.savefig(p4, dpi=150)
    plt.close(fig)
    generated.append(p4)

    return generated


def format_top_languages_table(top10_linguagens, total):
    lines = [
        "| Posição | Linguagem | Quantidade | Percentual |",
        "|---|---|---:|---:|",
    ]
    for i, (lang, count) in enumerate(top10_linguagens, start=1):
        pct = (count / total) * 100 if total else 0
        lines.append(f"| {i} | {lang} | {count} | {pct:.2f}% |")
    return "\n".join(lines)


def format_rq_table(metrics, hypotheses):
    return "\n".join([
        "| RQ | Métrica analisada | Resultado numérico | Resposta |",
        "|---|---|---|---|",
        f"| RQ01 | Mediana da idade dos repositórios | {metrics['idade_mediana_anos']:.2f} anos | {'Sim' if hypotheses['RQ01'][0] else 'Não'} |",
        f"| RQ02 | Mediana de PRs merged | {metrics['prs_mediana']:.0f} | {'Sim' if hypotheses['RQ02'][0] else 'Não'} |",
        f"| RQ03 | Mediana de releases | {metrics['releases_mediana']:.0f} | {'Sim' if hypotheses['RQ03'][0] else 'Não'} |",
        f"| RQ04 | Mediana de dias desde atualização | {metrics['dias_desde_update_mediana']:.0f} dias | {'Sim' if hypotheses['RQ04'][0] else 'Não'} |",
        f"| RQ05 | Top linguagens | {', '.join([x[0] for x in metrics['top10_linguagens'][:5]])} | {'Sim' if hypotheses['RQ05'][0] else 'Não'} |",
        f"| RQ06 | Mediana da razão de issues fechadas | {metrics['issues_ratio_mediana']:.2%} | {'Sim' if hypotheses['RQ06'][0] else 'Não'} |",
    ])


def build_report(metrics, hypotheses, chart_paths):
    now = datetime.now().strftime("%d/%m/%Y")
    chart_rel = [os.path.relpath(p, SPRINT3_DIR).replace("\\", "/") for p in chart_paths]

    report = f"""# Características de Repositórios Populares no GitHub (Sprint 3)

## Autores

- Kaio Henrique Oliveira da Silveira Barbosa

## Introdução

Este relatório final consolida os resultados do estudo sobre repositórios populares no GitHub, com base em 1000 repositórios coletados via API GraphQL. O foco é responder as questões de pesquisa (RQs) propostas no projeto.

## Questões de pesquisa e hipóteses

- **RQ01**: Sistemas populares são maduros/antigos?
  - Hipótese: sistemas populares tendem a ser mais antigos.
- **RQ02**: Sistemas populares recebem muita contribuição externa?
  - Hipótese: sistemas populares apresentam alto volume de PRs aceitas.
- **RQ03**: Sistemas populares lançam releases com frequência?
  - Hipótese: sistemas populares lançam releases regularmente.
- **RQ04**: Sistemas populares são atualizados com frequência?
  - Hipótese: sistemas populares são atualizados recentemente.
- **RQ05**: Sistemas populares são escritos nas linguagens mais populares?
  - Hipótese: linguagens predominantes incluem JavaScript, Python, Java e TypeScript.
- **RQ06**: Sistemas populares possuem alto percentual de issues fechadas?
  - Hipótese: percentual de fechamento de issues é alto.

## Objetivo

Responder quantitativamente às 6 RQs com base nos dados coletados nas sprints anteriores, usando análise estatística descritiva e visualizações.

## Metodologia

1. Leitura do arquivo CSV da Sprint 2 (`docs/Sprint2/repositorios.csv`).
2. Limpeza e normalização dos dados numéricos.
3. Cálculo de métricas centrais (média e mediana) por RQ.
4. Geração de gráficos de distribuição e frequência.
5. Interpretação dos resultados e decisão sobre as hipóteses.

### Regras de decisão adotadas

- RQ01: hipótese confirmada se mediana da idade >= 5 anos.
- RQ02: hipótese confirmada se mediana de PRs merged >= 100.
- RQ03: hipótese confirmada se mediana de releases >= 10.
- RQ04: hipótese confirmada se mediana de dias desde atualização <= 30.
- RQ05: hipótese confirmada se ao menos 3 linguagens esperadas (JS/Python/Java/TS) aparecem no top 10.
- RQ06: hipótese confirmada se mediana da razão de issues fechadas >= 80%.

## Resultados

### Tabela de respostas das RQs

{format_rq_table(metrics, hypotheses)}

### Tabela de linguagens (Top 10)

{format_top_languages_table(metrics['top10_linguagens'], metrics['total_repos'])}

### Métricas gerais

- Total de repositórios analisados: **{metrics['total_repos']}**
- Faixa de estrelas: **{metrics['estrelas_min']:,}** a **{metrics['estrelas_max']:,}**
- Média de estrelas: **{metrics['estrelas_media']:.0f}**
- Média de idade: **{metrics['idade_media_anos']:.2f} anos**
- Média de PRs merged: **{metrics['prs_media']:.0f}**
- Média de releases: **{metrics['releases_media']:.2f}**
- Média de dias desde atualização: **{metrics['dias_desde_update_media']:.2f} dias**
- Média da razão de issues fechadas: **{metrics['issues_ratio_media']:.2%}**

### Gráficos

"""

    if chart_rel:
        for rel in chart_rel:
            title = os.path.basename(rel).replace("_", " ").replace(".png", "").title()
            report += f"\n#### {title}\n\n![{title}]({rel})\n"
    else:
        report += "\n_Gráficos não gerados (matplotlib não instalado)._\n"

    report += f"""

## Discussões (insights)

- A mediana de idade indica o nível de maturidade dos projetos mais populares.
- A distribuição de PRs merged sugere presença de forte colaboração externa em parte dos projetos, mas com assimetria entre eles.
- A distribuição de releases mostra que popularidade não implica necessariamente alta frequência de versões formais.
- O tempo desde a última atualização aponta o quão ativos os projetos estão atualmente.
- A distribuição de linguagens confirma concentração em poucas tecnologias amplamente adotadas.
- A razão de issues fechadas permite avaliar o nível de manutenção/saúde operacional.

## Conclusão e tomadas de decisão (hipóteses)

- **RQ01**: {'Hipótese confirmada' if hypotheses['RQ01'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ01'][1]}).
- **RQ02**: {'Hipótese confirmada' if hypotheses['RQ02'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ02'][1]}).
- **RQ03**: {'Hipótese confirmada' if hypotheses['RQ03'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ03'][1]}).
- **RQ04**: {'Hipótese confirmada' if hypotheses['RQ04'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ04'][1]}).
- **RQ05**: {'Hipótese confirmada' if hypotheses['RQ05'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ05'][1]}).
- **RQ06**: {'Hipótese confirmada' if hypotheses['RQ06'][0] else 'Hipótese rejeitada'} ({hypotheses['RQ06'][1]}).

---

Relatório gerado automaticamente em {now}.
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)


def main():
    os.makedirs(SPRINT3_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    rows = load_data(CSV_PATH)
    if not rows:
        raise RuntimeError("CSV vazio. Execute a Sprint 2 para gerar dados.")

    metrics = compute_metrics(rows)
    hypotheses = evaluate_hypotheses(metrics)
    chart_paths = generate_charts(metrics)
    build_report(metrics, hypotheses, chart_paths)

    print("\n=== Sprint 3 finalizada ===")
    print(f"Repositórios analisados: {metrics['total_repos']}")
    print(f"Relatório gerado em: {REPORT_PATH}")
    if chart_paths:
        print("Gráficos gerados:")
        for p in chart_paths:
            print(f"- {p}")
    else:
        print("Gráficos não gerados (instale matplotlib).")


if __name__ == "__main__":
    main()
