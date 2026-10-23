"""Processamento repositorio a repositorio com retomada.

Cada resultado e gravado no CSV assim que sai. Se a execucao for interrompida
(cota esgotada, queda de rede, Ctrl+C), rodar de novo pula os repositorios que
ja estao no arquivo.
"""

from __future__ import annotations

import csv
import json
import os
import threading
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Callable, Iterable

TRABALHADORES_PADRAO = 4  # repositorios ao mesmo tempo: ja passa da cota de 5.000/h sem esgotar a memoria


def gravar_json(caminho: Path, dados: Any) -> None:
    """Grava o JSON num arquivo temporario e so depois o move para o lugar.

    Se a coleta for interrompida no meio da gravacao, o arquivo anterior (ou
    nenhum) continua la, e nunca um JSON pela metade que quebraria a retomada.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(f"{caminho.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    temporario.write_text(json.dumps(dados), encoding="utf-8")
    os.replace(temporario, caminho)


def processar_em_paralelo(
    itens: list,
    processar: Callable[[Any, Any], None],
    client: Any,
    trabalhadores: int = TRABALHADORES_PADRAO,
    progresso: Callable[[int, int], None] | None = None,
) -> None:
    """Chama `processar(client_da_thread, item)` para cada item, `trabalhadores` por vez.

    A coleta e limitada pelo tempo de resposta da API, e nao pela cota: uma
    chamada por vez usa so uma fracao das 5.000 requisicoes por hora. Cada
    thread usa a sua propria copia do cliente (`client.copia()`, se existir),
    porque uma sessao HTTP nao deve ser compartilhada entre threads. Se um item
    falhar, os que ainda nao comecaram sao cancelados e o erro e propagado.
    """
    if not itens:
        return
    locais = threading.local()

    def cliente_da_thread():
        if not hasattr(locais, "client"):
            locais.client = client.copia() if hasattr(client, "copia") else client
        return locais.client

    executor = ThreadPoolExecutor(max_workers=max(1, trabalhadores))
    try:
        futuros = [executor.submit(lambda item=item: processar(cliente_da_thread(), item)) for item in itens]
        feitos = 0
        pendentes = set(futuros)
        while pendentes:
            prontos, pendentes = wait(pendentes, return_when=FIRST_EXCEPTION)
            for futuro in prontos:
                futuro.result()  # propaga o erro do item, se houver
                feitos += 1
                if progresso:
                    progresso(feitos, len(itens))
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


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
