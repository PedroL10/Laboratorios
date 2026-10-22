"""Tempo de recuperacao apos uma execucao de CI/CD com falha (RQ 04).

As execucoes de **um mesmo workflow** (`workflow_id`) sao ordenadas pelo
inicio. Um **episodio de falha** comeca na primeira falha apos um sucesso e
termina na proxima execucao bem-sucedida do mesmo workflow. O tempo de
recuperacao do episodio e:

    updated_at do sucesso - run_started_at da primeira falha

O valor do repositorio e a mediana, em horas, de todos os episodios de todos os
seus workflows. Runs ignorados pela tabela de `conclusion` (ver
`metricas.cfr_ci`) nao abrem nem fecham episodios.

Dois casos nao entram na mediana, mas sao contados:
- **censurado:** o episodio nao termina dentro da janela (a falha nunca foi
  corrigida ate o fim da observacao). Descarta-lo sem registro faria o
  repositorio parecer mais rapido do que e; por isso a proporcao de episodios
  censurados e reportada.
- **sem inicio observado:** o workflow ja comeca a janela falhando. Pela
  definicao, o episodio comeca na primeira falha *apos um sucesso*, e esse
  sucesso ficou antes da janela, entao o inicio real do episodio e
  desconhecido.

Cada run e um dicionario com `workflow_id`, `conclusion`, `run_started_at`
(ou, na falta dele, `created_at`) e `updated_at`.
"""

from __future__ import annotations

import statistics
from datetime import datetime

from metricas.cfr_ci import FALHA, SUCESSO, classificar_conclusao


def _parse(data_iso: str) -> datetime:
    return datetime.fromisoformat(data_iso.replace("Z", "+00:00"))


def _inicio(run: dict) -> str:
    return run.get("run_started_at") or run["created_at"]


def horas(data_fim: datetime, data_inicio: datetime) -> float:
    """Diferenca entre duas datas, em horas (pode ter fracao)."""
    return (data_fim - data_inicio).total_seconds() / 3600


def episodios_do_workflow(runs: list[dict]) -> dict:
    """Episodios de falha de um unico workflow.

    Devolve `{"duracoes_horas": [...], "censurados": n, "sem_inicio": n}`.
    """
    duracoes: list[float] = []
    sem_inicio = 0
    ultimo: str | None = None  # SUCESSO ou FALHA do ultimo run valido
    inicio_episodio: datetime | None = None

    for run in sorted(runs, key=_inicio):
        classe = classificar_conclusao(run.get("conclusion"))
        if classe == FALHA:
            if ultimo == SUCESSO:
                inicio_episodio = _parse(_inicio(run))
            elif ultimo is None:
                sem_inicio = 1
            ultimo = FALHA
        elif classe == SUCESSO:
            if inicio_episodio is not None:
                duracoes.append(horas(_parse(run["updated_at"]), inicio_episodio))
                inicio_episodio = None
            ultimo = SUCESSO

    return {
        "duracoes_horas": duracoes,
        "censurados": 1 if inicio_episodio is not None else 0,
        "sem_inicio": sem_inicio,
    }


def recuperacao_repositorio(runs: list[dict]) -> dict:
    """Agrega os episodios de todos os workflows de um repositorio.

    `tempo_recuperacao_horas` e None quando nenhum episodio terminou na janela.
    `proporcao_censurados` e None quando nao houve nenhum episodio.
    """
    por_workflow: dict = {}
    for run in runs:
        por_workflow.setdefault(run["workflow_id"], []).append(run)

    duracoes: list[float] = []
    censurados = 0
    sem_inicio = 0
    for runs_workflow in por_workflow.values():
        episodios = episodios_do_workflow(runs_workflow)
        duracoes.extend(episodios["duracoes_horas"])
        censurados += episodios["censurados"]
        sem_inicio += episodios["sem_inicio"]

    n_episodios = len(duracoes) + censurados
    return {
        "tempo_recuperacao_horas": statistics.median(duracoes) if duracoes else None,
        "n_episodios": len(duracoes),
        "n_episodios_censurados": censurados,
        "proporcao_censurados": censurados / n_episodios if n_episodios else None,
        "n_episodios_sem_inicio": sem_inicio,
    }
