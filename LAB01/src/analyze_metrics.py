"""Calcula as metricas das RQs a partir do CSV coletado (Sprint 3).

Uso:
    python src/analyze_metrics.py
    python src/analyze_metrics.py --reference-at 2026-08-24T00:00:00Z

Este script e a fonte oficial e reprodutivel dos numeros usados no relatorio:
antes dele, resultados/resultados_metricas_1000.json era preenchido manualmente.
Nenhuma biblioteca de terceiros consulta a API do GitHub aqui - o script so le
o CSV ja coletado por src/collect_repositories.py.
"""

import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone

DEFAULT_INPUT = os.path.join(os.path.dirname(__file__), "..", "data", "repositorios_lab01_s02.csv")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "resultados", "resultados_metricas_1000.json")

NAO_INFORMADO = "Nao informado"
# Data usada na primeira analise da Sprint 3. Manter a referencia fixa torna
# RQ01 (idade) e RQ04 (tempo desde o ultimo push) reproduziveis.
DEFAULT_REFERENCE_AT = "2026-08-24T00:00:00Z"


def load_repositories(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_iso(dt_str):
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _round(value, digits=2):
    return round(value, digits) if value is not None else None


def analyze_rq01_idade(repos, now):
    idades_dias = [(now - _parse_iso(r["created_at"])).days for r in repos]
    return {
        "mediana_dias": _round(statistics.median(idades_dias), 1),
        "media_dias": _round(statistics.mean(idades_dias)),
        "mediana_anos": _round(statistics.median(idades_dias) / 365, 1),
        "min_dias": min(idades_dias),
        "max_dias": max(idades_dias),
    }


def analyze_rq02_prs(repos):
    prs = [int(r["pull_requests_merged_total"]) for r in repos]
    return {
        "mediana": statistics.median(prs),
        "media": _round(statistics.mean(prs)),
        "min": min(prs),
        "max": max(prs),
    }


def analyze_rq03_releases(repos):
    releases = [int(r["releases_total"]) for r in repos]
    sem_release = sum(1 for r in releases if r == 0)
    return {
        "mediana": statistics.median(releases),
        "media": _round(statistics.mean(releases)),
        "min": min(releases),
        "max": max(releases),
        "sem_release_percentual": _round(100 * sem_release / len(releases), 1),
    }


def analyze_rq04_atualizacao(repos, now):
    dias_sem_update = [(now - _parse_iso(r["pushed_at"])).days for r in repos]
    return {
        "mediana_dias": statistics.median(dias_sem_update),
        "media_dias": _round(statistics.mean(dias_sem_update)),
        "min_dias": min(dias_sem_update),
        "max_dias": max(dias_sem_update),
    }


def _linguagem(r):
    return r["primary_language"] or NAO_INFORMADO


def _percentuais_issues_fechadas(repos):
    """Retorna percentuais por repositorio, ignorando trackers sem issues."""
    return [
        100 * int(r["issues_closed_total"]) / int(r["issues_total"])
        for r in repos
        if int(r["issues_total"]) > 0
    ]


def analyze_rq05_linguagem(repos, top_n=10):
    contagem = {}
    for r in repos:
        lang = _linguagem(r)
        contagem[lang] = contagem.get(lang, 0) + 1

    distribuicao = sorted(contagem.items(), key=lambda kv: kv[1], reverse=True)
    total = len(repos)
    return {
        "distribuicao_top10": [
            {"linguagem": lang, "quantidade": qtd, "percentual": _round(100 * qtd / total, 1)}
            for lang, qtd in distribuicao[:top_n]
        ],
        "total_linguagens_distintas": len(contagem),
    }


def analyze_rq06_issues_fechadas(repos):
    percentuais = _percentuais_issues_fechadas(repos)

    return {
        "mediana_percentual": _round(statistics.median(percentuais), 1),
        "media_percentual": _round(statistics.mean(percentuais), 1),
        "repositorios_sem_issues": len(repos) - len(percentuais),
    }


def analyze_rq07_por_linguagem(repos, now, min_repos=10):
    """Compara apenas grupos com tamanho suficiente para interpretacao.

    O limiar de 10 evita que uma unica observacao pareca representar uma
    linguagem inteira. O tamanho de cada grupo segue no resultado.
    """
    por_lang = {}
    for r in repos:
        por_lang.setdefault(_linguagem(r), []).append(r)

    resultado = {}
    for lang, grupo in sorted(por_lang.items(), key=lambda kv: len(kv[1]), reverse=True):
        if len(grupo) < min_repos:
            continue
        prs = [int(r["pull_requests_merged_total"]) for r in grupo]
        releases = [int(r["releases_total"]) for r in grupo]
        dias_sem_update = [(now - _parse_iso(r["pushed_at"])).days for r in grupo]
        resultado[lang] = {
            "quantidade_repos": len(grupo),
            "mediana_prs_aceitas": statistics.median(prs),
            "mediana_releases": statistics.median(releases),
            "mediana_dias_sem_update": statistics.median(dias_sem_update),
        }
    return resultado


def _resumo_manutencao(repos, now):
    """Indicadores comuns usados na comparacao da RQ08."""
    if not repos:
        return {
            "quantidade_repos": 0,
            "mediana_prs_aceitas": None,
            "mediana_releases": None,
            "mediana_dias_sem_update": None,
            "mediana_percentual_issues_fechadas": None,
            "repositorios_sem_issues": 0,
        }

    percentuais = _percentuais_issues_fechadas(repos)
    prs = [int(r["pull_requests_merged_total"]) for r in repos]
    releases = [int(r["releases_total"]) for r in repos]
    dias_sem_update = [(now - _parse_iso(r["pushed_at"])).days for r in repos]
    return {
        "quantidade_repos": len(repos),
        "mediana_prs_aceitas": statistics.median(prs),
        "mediana_releases": statistics.median(releases),
        "mediana_dias_sem_update": statistics.median(dias_sem_update),
        "mediana_percentual_issues_fechadas": _round(statistics.median(percentuais), 1)
        if percentuais else None,
        "repositorios_sem_issues": len(repos) - len(percentuais),
    }


def analyze_rq08_sem_linguagem(repos, now):
    """RQ08: contrasta repositorios com e sem linguagem primaria informada."""
    sem_linguagem = [r for r in repos if _linguagem(r) == NAO_INFORMADO]
    com_linguagem = [r for r in repos if _linguagem(r) != NAO_INFORMADO]
    return {
        "definicao_grupo_sem_linguagem": (
            "primaryLanguage nulo na resposta GraphQL; nao implica ausencia de codigo"
        ),
        "sem_linguagem": _resumo_manutencao(sem_linguagem, now),
        "com_linguagem": _resumo_manutencao(com_linguagem, now),
    }


def analyze_data_quality(repos):
    """Registra verificacoes simples para tornar a analise auditavel."""
    nomes = [r["name_with_owner"] for r in repos]
    return {
        "duplicados": len(nomes) - len(set(nomes)),
        "linguagem_primaria_nao_informada": sum(
            1 for r in repos if _linguagem(r) == NAO_INFORMADO
        ),
        "repositorios_sem_issues": sum(
            1 for r in repos if int(r["issues_total"]) == 0
        ),
        "issues_fechadas_maior_que_total": sum(
            1
            for r in repos
            if int(r["issues_closed_total"]) > int(r["issues_total"])
        ),
    }


def analyze(repos, now):
    return {
        "total_repositorios": len(repos),
        "analysis_reference_at": now.isoformat().replace("+00:00", "Z"),
        "qualidade_dados": analyze_data_quality(repos),
        "RQ01_idade": analyze_rq01_idade(repos, now),
        "RQ02_prs_aceitas": analyze_rq02_prs(repos),
        "RQ03_releases": analyze_rq03_releases(repos),
        "RQ04_atualizacao": analyze_rq04_atualizacao(repos, now),
        "RQ05_linguagem": analyze_rq05_linguagem(repos),
        "RQ06_issues_fechadas": analyze_rq06_issues_fechadas(repos),
        "RQ07_por_linguagem": analyze_rq07_por_linguagem(repos, now),
        "RQ08_sem_linguagem": analyze_rq08_sem_linguagem(repos, now),
    }


def parse_args(args):
    """Aceita caminhos posicionais e uma data de referencia explicita."""
    input_path = DEFAULT_INPUT
    output_path = DEFAULT_OUTPUT
    reference_at = DEFAULT_REFERENCE_AT
    paths = []
    index = 0

    while index < len(args):
        argument = args[index]
        if argument == "--reference-at":
            index += 1
            if index == len(args):
                raise ValueError("--reference-at exige uma data ISO 8601")
            reference_at = args[index]
        elif argument.startswith("--reference-at="):
            reference_at = argument.split("=", 1)[1]
        elif argument.startswith("-"):
            raise ValueError(f"Opcao desconhecida: {argument}")
        else:
            paths.append(argument)
        index += 1

    if len(paths) > 2:
        raise ValueError("Informe no maximo: [entrada.csv] [saida.json]")
    if paths:
        input_path = paths[0]
    if len(paths) == 2:
        output_path = paths[1]

    return input_path, output_path, _parse_iso(reference_at)


if __name__ == "__main__":
    input_path, output_path, reference_at = parse_args(sys.argv[1:])
    repositories = load_repositories(input_path)
    metrics = analyze(repositories, reference_at)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(
        f"Metricas de {metrics['total_repositorios']} repositorios salvas em {output_path} "
        f"(referencia: {metrics['analysis_reference_at']})"
    )
