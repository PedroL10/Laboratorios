"""Change failure rate, variante (a): proxy de CI (RQ 03).

CFR (a) = falhas / (falhas + sucessos), sobre os workflow runs de push no
default branch dentro da janela. A classificacao segue a tabela de
`conclusion` da secao 3 do enunciado:

| conclusion                                       | tratamento |
| ------------------------------------------------ | ---------- |
| success                                          | sucesso    |
| failure, timed_out, startup_failure              | falha      |
| cancelled, skipped, neutral, action_required,    | ignorado   |
| stale, ou vazio (execucao em andamento)          |            |

Essa variante mede falha de **pipeline**, nao falha em producao: um teste
quebrado no main conta como falha mesmo que nada tenha chegado ao usuario.

Cada run e um dicionario com, ao menos, a chave `conclusion`.
"""

from __future__ import annotations

CONCLUSOES_SUCESSO = {"success"}
CONCLUSOES_FALHA = {"failure", "timed_out", "startup_failure"}
CONCLUSOES_VALIDAS = CONCLUSOES_SUCESSO | CONCLUSOES_FALHA

SUCESSO = "sucesso"
FALHA = "falha"
IGNORADO = "ignorado"


def classificar_conclusao(conclusion: str | None) -> str:
    """Classifica o `conclusion` de um run em sucesso, falha ou ignorado."""
    if conclusion in CONCLUSOES_SUCESSO:
        return SUCESSO
    if conclusion in CONCLUSOES_FALHA:
        return FALHA
    return IGNORADO


def cfr_ci_repositorio(runs: list[dict]) -> dict:
    """CFR variante (a) de um repositorio, somando todos os seus workflows.

    `cfr_ci` e None quando nao ha nenhum run valido (sucesso ou falha).
    """
    contagem = {SUCESSO: 0, FALHA: 0, IGNORADO: 0}
    for run in runs:
        contagem[classificar_conclusao(run.get("conclusion"))] += 1

    validos = contagem[SUCESSO] + contagem[FALHA]
    return {
        "cfr_ci": contagem[FALHA] / validos if validos else None,
        "n_runs_falha": contagem[FALHA],
        "n_runs_sucesso": contagem[SUCESSO],
        "n_runs_ignorados": contagem[IGNORADO],
    }
