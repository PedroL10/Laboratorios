"""Processamento repositorio a repositorio com retomada.

Cada resultado e gravado no CSV assim que sai. Se a execucao for interrompida
(cota esgotada, queda de rede, Ctrl+C), rodar de novo pula os repositorios que
ja estao no arquivo.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Iterable


def carregar_processados(caminho: Path) -> dict[str, dict]:
    """Le o CSV de uma execucao anterior (se existir), indexado por `full_name`."""
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8", newline="") as f:
        return {linha["full_name"]: linha for linha in csv.DictReader(f)}


def processar_com_retomada(
    repositorios: Iterable[dict],
    processar: Callable[[dict], dict],
    caminho_saida: str | Path,
    campos: list[str],
    progresso: Callable[[int], None] | None = None,
    parar: Callable[[list[dict]], bool] | None = None,
) -> dict[str, dict]:
    """Aplica `processar` a cada repositorio ainda nao presente em `caminho_saida`.

    `parar(anteriores)` e consultado antes de cada repositorio pendente, com os
    resultados dos repositorios que vem antes dele na ordem de `repositorios`, e
    permite encerrar cedo (ex.: quando ja ha repositorios suficientes na amostra).
    Assim, um repositorio que ficou pendente no meio da lista (ex.: erro temporario)
    e processado numa retomada mesmo que os seguintes ja estejam no arquivo.
    Devolve todos os resultados (anteriores + novos), indexados por `full_name`.
    """
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    processados = carregar_processados(caminho_saida)

    novo_arquivo = not caminho_saida.exists()
    with caminho_saida.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        if novo_arquivo:
            writer.writeheader()
        feitos = 0
        anteriores: list[dict] = []
        for repo in repositorios:
            if repo["full_name"] in processados:
                anteriores.append(processados[repo["full_name"]])
                continue
            if parar and parar(anteriores):
                break
            linha = processar(repo)
            writer.writerow(linha)
            f.flush()
            processados[linha["full_name"]] = linha
            anteriores.append(linha)
            feitos += 1
            if progresso:
                progresso(feitos)

    return processados
