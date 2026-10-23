"""Validacao manual (secao 6) - heuristica de release corretiva frente aos rotulos.

Le os rotulos de cada avaliador (CSV baixado da pagina de rotulagem) e os dados
completos das releases sorteadas (`dados_rotulagem.json`, com as mensagens de
todos os commits), aplica a heuristica automatica de `metricas.cfr` e grava em
`resultados/amostra_ouro/validacao.md`:

- precisao, recall e F1 da heuristica, com intervalo de 95% por bootstrap;
- matriz de confusao e o desempenho de cada pista da heuristica separada
  (so patch-only no SemVer; so palavra-chave), para orientar o refinamento;
- distribuicao dos rotulos de tipo do projeto e de "entregas reais".

Com tres avaliadores, calcula tambem o kappa de Fleiss em cada dimensao e usa
o voto da maioria como consenso. Com um unico avaliador, os rotulos dele sao a
referencia e o kappa nao se aplica (isso precisa ser declarado no artigo).

Uso:
    python -m analise.amostra_ouro --rotulos resultados/amostra_ouro_pedro.csv
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from analise.comum import carregar, fmt, markdown
from metricas.cfr import avaliar_heuristica, eh_corretiva, eh_patch_only, tem_commit_com_palavra_chave

REPETICOES_BOOTSTRAP = 2000


def consenso(valores: list[str]) -> str | None:
    """Voto da maioria; None em empate sem maioria (ex.: 1-1-1), a decidir em reuniao."""
    contagem = Counter(v for v in valores if v)
    if not contagem:
        return None
    (mais_votado, votos), *resto = contagem.most_common()
    if resto and resto[0][1] == votos:
        return None
    return mais_votado


def fleiss_kappa_dimensao(rotulos_por_item: list[list[str]]) -> float | None:
    """Kappa de Fleiss (statsmodels) para itens rotulados por todos os avaliadores."""
    from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

    completos = [r for r in rotulos_por_item if all(r)]
    if len(completos) < 2:
        return None
    categorias = sorted({c for r in completos for c in r})
    if len(categorias) < 2:
        return None  # todos deram a mesma resposta: kappa indefinido (0/0)
    tabela, _ = aggregate_raters([[categorias.index(c) for c in r] for r in completos])
    return float(fleiss_kappa(tabela))


def intervalo_bootstrap(heuristica: list[bool], referencia: list[bool], seed: int = 42) -> dict:
    """Intervalo de 95% (percentis 2,5 e 97,5) de precisao, recall e F1 por bootstrap."""
    rng = random.Random(seed)
    n = len(heuristica)
    amostras: dict[str, list[float]] = {"precisao": [], "recall": [], "f1": []}
    for _ in range(REPETICOES_BOOTSTRAP):
        indices = [rng.randrange(n) for _ in range(n)]
        resultado = avaliar_heuristica([heuristica[i] for i in indices], [referencia[i] for i in indices])
        for chave, valor in resultado.items():
            if valor is not None:
                amostras[chave].append(valor)
    intervalo = {}
    for chave, valores in amostras.items():
        valores.sort()
        intervalo[chave] = (
            (valores[int(0.025 * len(valores))], valores[int(0.975 * len(valores)) - 1]) if valores else (None, None)
        )
    return intervalo


def matriz_confusao(heuristica: list[bool], referencia: list[bool]) -> dict:
    return {
        "vp": sum(1 for h, r in zip(heuristica, referencia) if h and r),
        "fp": sum(1 for h, r in zip(heuristica, referencia) if h and not r),
        "fn": sum(1 for h, r in zip(heuristica, referencia) if not h and r),
        "vn": sum(1 for h, r in zip(heuristica, referencia) if not h and not r),
    }


def avaliar(dados: list[dict], avaliadores: dict[str, list[dict]]) -> dict:
    """Junta os rotulos dos avaliadores e avalia a heuristica frente a referencia."""
    nomes = list(avaliadores)
    por_release = {nome: {(l["full_name"], l["tag_name"]): l for l in linhas} for nome, linhas in avaliadores.items()}

    itens = []
    for d in dados:
        chave = (d["full_name"], d["tag_name"])
        votos = [por_release[n].get(chave, {}).get("corretiva", "") for n in nomes]
        itens.append({"dados": d, "votos": votos, "referencia": consenso(votos)})

    avaliados = [i for i in itens if i["referencia"] in ("sim", "nao")]
    referencia = [i["referencia"] == "sim" for i in avaliados]
    heuristica = [eh_corretiva(i["dados"]) for i in avaliados]
    so_patch = [eh_patch_only(i["dados"]["tag_anterior"], i["dados"]["tag_name"]) for i in avaliados]
    so_palavra = [tem_commit_com_palavra_chave(i["dados"]["mensagens_commits"]) for i in avaliados]

    repos = {}
    for nome in nomes:
        for linha in avaliadores[nome]:
            repos.setdefault(linha["full_name"], {}).setdefault(nome, linha)
    tipos = [consenso([repos[r].get(n, {}).get("tipo_projeto", "") for n in nomes]) for r in repos]
    entregas = [consenso([repos[r].get(n, {}).get("releases_representam_entrega_real", "") for n in nomes]) for r in repos]

    kappas = None
    if len(nomes) >= 2:
        kappas = {
            "corretiva": fleiss_kappa_dimensao([i["votos"] for i in itens]),
            "tipo_projeto": fleiss_kappa_dimensao(
                [[repos[r].get(n, {}).get("tipo_projeto", "") for n in nomes] for r in repos]),
            "entrega_real": fleiss_kappa_dimensao(
                [[repos[r].get(n, {}).get("releases_representam_entrega_real", "") for n in nomes] for r in repos]),
        }

    return {
        "avaliadores": nomes,
        "n_releases": len(itens),
        "n_avaliadas": len(avaliados),
        "n_sem_referencia": len(itens) - len(avaliados),
        "n_corretivas": sum(referencia),
        "heuristica": avaliar_heuristica(heuristica, referencia) if avaliados else None,
        "intervalo": intervalo_bootstrap(heuristica, referencia) if avaliados else None,
        "confusao": matriz_confusao(heuristica, referencia),
        "so_patch": avaliar_heuristica(so_patch, referencia) if avaliados else None,
        "so_palavra": avaliar_heuristica(so_palavra, referencia) if avaliados else None,
        "tipos": Counter(t or "(sem rotulo)" for t in tipos),
        "entregas": Counter(e or "(sem rotulo)" for e in entregas),
        "n_repos": len(repos),
        "kappas": kappas,
    }


def relatorio(r: dict) -> str:
    def linha(nome, m, ic=None):
        if m is None:
            return [nome, "-", "-", "-"]
        texto = [fmt(m["precisao"]), fmt(m["recall"]), fmt(m["f1"])]
        if ic:
            texto = [f"{t} ({fmt(ic[k][0])}–{fmt(ic[k][1])})" for t, k in zip(texto, ["precisao", "recall", "f1"])]
        return [nome, *texto]

    c = r["confusao"]
    partes = [
        "# Validacao manual da heuristica de release corretiva\n",
        f"Avaliador(es): {', '.join(r['avaliadores'])}. Releases sorteadas: {r['n_releases']}; "
        f"com rotulo de referencia: {r['n_avaliadas']} ({r['n_corretivas']} corretivas); "
        f"sem referencia (sem rotulo ou empate): {r['n_sem_referencia']}. Repositorios: {r['n_repos']}.\n",
        "## Desempenho (intervalo de 95% por bootstrap)\n",
        markdown(
            ["Heuristica", "Precisao", "Recall", "F1"],
            [
                linha("Completa: patch-only OU palavra-chave", r["heuristica"], r["intervalo"]),
                linha("So patch-only no SemVer", r["so_patch"]),
                linha("So palavra-chave (revert/hotfix/fix)", r["so_palavra"]),
            ],
        ),
        "\n## Matriz de confusao (heuristica completa)\n",
        markdown(
            ["", "Referencia: corretiva", "Referencia: nao corretiva"],
            [["Heuristica: corretiva", str(c["vp"]), str(c["fp"])],
             ["Heuristica: nao corretiva", str(c["fn"]), str(c["vn"])]],
        ),
        "\n## Rotulos por repositorio\n",
        markdown(["Tipo do projeto", "Repositorios"], [[k, str(v)] for k, v in r["tipos"].most_common()]),
        "\n" + markdown(["Releases sao entregas reais?", "Repositorios"], [[k, str(v)] for k, v in r["entregas"].most_common()]),
    ]
    if r["kappas"]:
        partes += [
            "\n## Concordancia entre avaliadores (kappa de Fleiss)\n",
            markdown(["Dimensao", "Kappa"], [[k, fmt(v, 3)] for k, v in r["kappas"].items()]),
        ]
    else:
        partes.append(
            "\nUm unico avaliador: os rotulos dele sao a referencia e a concordancia entre "
            "avaliadores (kappa de Fleiss) nao pode ser calculada.\n"
        )
    return "\n".join(partes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rotulos", nargs="+", required=True, help="Um CSV de rotulos por avaliador")
    parser.add_argument("--dados", default="resultados/amostra_ouro/dados_rotulagem.json")
    parser.add_argument("--saida", default="resultados/amostra_ouro")
    args = parser.parse_args(argv)

    dados = json.loads(Path(args.dados).read_text(encoding="utf-8"))
    avaliadores = {Path(c).stem.removeprefix("amostra_ouro_"): carregar(c) for c in args.rotulos}
    resultado = avaliar(dados, avaliadores)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "validacao.md").write_text(relatorio(resultado), encoding="utf-8")

    h = resultado["heuristica"] or {}
    print(f"{resultado['n_avaliadas']} releases avaliadas: precisao={fmt(h.get('precisao'))} "
          f"recall={fmt(h.get('recall'))} F1={fmt(h.get('f1'))}")
    print(f"Relatorio salvo em {saida / 'validacao.md'}")


if __name__ == "__main__":
    main()
