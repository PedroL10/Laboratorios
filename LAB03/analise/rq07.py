"""RQ 07 - o quanto a classificacao DORA depende da definicao operacional.

Classifica cada repositorio sob as combinacoes C1, C2 e C3 (ver
`metricas.sensibilidade`) e compara, para cada par, a % de repositorios que
mudam de categoria e o kappa de Cohen ponderado linear -- na classificacao
geral e em cada metrica.

Grava em `resultados/rq07/`:
- `classificacoes.csv`: as categorias de cada repositorio nas tres combinacoes;
- `distribuicao.md`: quantos repositorios em cada categoria geral, por combinacao;
- `concordancia.md` / `.csv`: % que mudou e kappa ponderado por par e por metrica;
- `figuras/distribuicao.png`: distribuicao da categoria geral em C1, C2 e C3;
- `figuras/transicoes.png`: de -> para da categoria geral em cada par.

Uso:
    python -m analise.rq07 --entrada resultados/amostra_metricas.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analise.comum import (
    CORES_CATEGORIA,
    GRADE,
    SUPERFICIE,
    TEXTO,
    TEXTO_SECUNDARIO,
    carregar,
    estilo_eixo,
    fmt,
    markdown,
    salvar_csv,
)
from metricas.descritiva import CATEGORIAS, distribuicao_categorias
from metricas.sensibilidade import (
    COMBINACOES,
    DESCRICAO_COMBINACOES,
    PARES,
    classificar_combinacao,
    comparar_classificacoes,
    interpretar_kappa,
)

import matplotlib.pyplot as plt  # noqa: E402  (depois de analise.comum, que escolhe o backend)
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

DIMENSOES = [
    ("categoria_geral", "Geral"),
    ("categoria_frequencia", "Deployment frequency"),
    ("categoria_lead_time", "Lead time"),
    ("categoria_cfr", "CFR"),
]

RAMPA_CONTAGEM = LinearSegmentedColormap.from_list("contagem", ["#f0f6fe", "#9ec5f4", "#3987e5", "#1c5cab", "#0d366b"])


def classificar_todos(repositorios: list[dict]) -> list[dict]:
    """Uma linha por repositorio com as categorias nas tres combinacoes."""
    linhas = []
    for repo in repositorios:
        linha = {"full_name": repo["full_name"]}
        for combinacao in COMBINACOES:
            categorias = classificar_combinacao(repo, combinacao)
            for coluna, _ in DIMENSOES:
                linha[f"{coluna}_{combinacao}"] = categorias[coluna]
        linhas.append(linha)
    return linhas


def tabela_concordancia(classificacoes: list[dict]) -> list[dict]:
    linhas = []
    for x, y in PARES:
        for coluna, rotulo in DIMENSOES:
            resultado = comparar_classificacoes(
                [c[f"{coluna}_{x}"] for c in classificacoes], [c[f"{coluna}_{y}"] for c in classificacoes]
            )
            linhas.append(
                {"par": f"{x} x {y}", "dimensao": rotulo, **resultado, "concordancia": interpretar_kappa(resultado["kappa"])}
            )
    return linhas


def figura_distribuicao(classificacoes: list[dict], caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 2.8), facecolor=SUPERFICIE)
    estilo_eixo(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRADE, linewidth=0.6)
    combinacoes = list(COMBINACOES)[::-1]
    rotulos = [f"{c}: {DESCRICAO_COMBINACOES[c]}" for c in combinacoes]
    esquerda = [0.0] * len(combinacoes)
    distribuicoes = [distribuicao_categorias([l[f"categoria_geral_{c}"] for l in classificacoes]) for c in combinacoes]
    for categoria in CATEGORIAS:
        larguras = [(d["proporcao"][categoria] or 0) * 100 for d in distribuicoes]
        barras = ax.barh(rotulos, larguras, left=esquerda, color=CORES_CATEGORIA[categoria],
                         edgecolor=SUPERFICIE, linewidth=2, height=0.6, label=categoria)
        for barra, largura in zip(barras, larguras):
            if largura >= 7:
                ax.text(barra.get_x() + largura / 2, barra.get_y() + barra.get_height() / 2, f"{largura:.0f}%",
                        ha="center", va="center", fontsize=7.5,
                        color="#ffffff" if categoria in ("Elite", "High") else TEXTO)
        esquerda = [e + l for e, l in zip(esquerda, larguras)]
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos repositórios classificados", fontsize=8, color=TEXTO_SECUNDARIO)
    ax.legend(ncols=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=8)
    ax.set_title("RQ 07 - Categoria DORA geral em cada combinação de definições", fontsize=11,
                 color=TEXTO, loc="left", pad=24)
    fig.tight_layout()
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def figura_transicoes(classificacoes: list[dict], concordancia: list[dict], caminho: Path) -> None:
    fig, eixos = plt.subplots(1, len(PARES), figsize=(11, 4.3), facecolor=SUPERFICIE)
    gerais = {c["par"]: c for c in concordancia if c["dimensao"] == "Geral"}
    for ax, (x, y) in zip(eixos, PARES):
        matriz = [[0] * len(CATEGORIAS) for _ in CATEGORIAS]
        for linha in classificacoes:
            de, para = linha[f"categoria_geral_{x}"], linha[f"categoria_geral_{y}"]
            if de and para:
                matriz[CATEGORIAS.index(de)][CATEGORIAS.index(para)] += 1
        maximo = max(1, max(max(l) for l in matriz))
        ax.imshow(matriz, cmap=RAMPA_CONTAGEM, vmin=0, vmax=maximo)
        for i, linha in enumerate(matriz):
            for j, valor in enumerate(linha):
                ax.text(j, i, str(valor), ha="center", va="center", fontsize=8.5,
                        color="#ffffff" if valor > 0.6 * maximo else TEXTO)
        ax.set_xticks(range(len(CATEGORIAS)), CATEGORIAS, fontsize=8, color=TEXTO)
        ax.set_yticks(range(len(CATEGORIAS)), CATEGORIAS, fontsize=8, color=TEXTO)
        ax.set_xticks([v - 0.5 for v in range(1, len(CATEGORIAS))], minor=True)
        ax.set_yticks([v - 0.5 for v in range(1, len(CATEGORIAS))], minor=True)
        ax.grid(which="minor", color=SUPERFICIE, linewidth=3)
        ax.tick_params(which="both", length=0)
        for lado in ax.spines.values():
            lado.set_visible(False)
        ax.set_xlabel(y, fontsize=9, color=TEXTO_SECUNDARIO)
        ax.set_ylabel(x, fontsize=9, color=TEXTO_SECUNDARIO)
        geral = gerais[f"{x} x {y}"]
        ax.set_title(f"{x} x {y}: {fmt((geral['pct_mudaram'] or 0) * 100, 0)}% mudaram, κ = {fmt(geral['kappa'])}",
                     fontsize=9, color=TEXTO, loc="left")
    fig.suptitle("RQ 07 - Transições da categoria geral entre combinações (diagonal = não mudou)",
                 fontsize=11, color=TEXTO, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    fig.savefig(caminho, dpi=200, bbox_inches="tight")
    plt.close(fig)


def gerar(entrada: str | Path, saida: str | Path) -> dict:
    repositorios = carregar(entrada)
    saida = Path(saida)
    (saida / "figuras").mkdir(parents=True, exist_ok=True)

    classificacoes = classificar_todos(repositorios)
    salvar_csv(classificacoes, saida / "classificacoes.csv")

    linhas_dist = []
    for combinacao in COMBINACOES:
        dist = distribuicao_categorias([c[f"categoria_geral_{combinacao}"] for c in classificacoes])
        linhas_dist.append(
            [f"{combinacao} ({DESCRICAO_COMBINACOES[combinacao]})",
             *[f"{dist['contagem'][k]} ({fmt((dist['proporcao'][k] or 0) * 100, 1)}%)" for k in CATEGORIAS],
             str(dist["sem_categoria"])]
        )
    (saida / "distribuicao.md").write_text(
        "# RQ 07 - Categoria DORA geral por combinacao de definicoes\n\n"
        + markdown(["Combinacao", *CATEGORIAS, "Sem categoria"], linhas_dist),
        encoding="utf-8",
    )

    concordancia = tabela_concordancia(classificacoes)
    salvar_csv(concordancia, saida / "concordancia.csv")
    (saida / "concordancia.md").write_text(
        "# RQ 07 - Concordancia entre combinacoes\n\n"
        "Kappa de Cohen ponderado (linear); concordancia segundo Landis & Koch (1977). "
        "So entram os repositorios classificados nas duas combinacoes do par.\n\n"
        + markdown(
            ["Par", "Dimensao", "n", "Mudaram", "% mudaram", "Kappa ponderado", "Concordancia"],
            [[c["par"], c["dimensao"], str(c["n"]), str(c["mudaram"]),
              fmt((c["pct_mudaram"] or 0) * 100 if c["pct_mudaram"] is not None else None, 1),
              fmt(c["kappa"], 3), c["concordancia"] or "-"] for c in concordancia],
        ),
        encoding="utf-8",
    )

    figura_distribuicao(classificacoes, saida / "figuras" / "distribuicao.png")
    figura_transicoes(classificacoes, concordancia, saida / "figuras" / "transicoes.png")
    return {"classificacoes": classificacoes, "concordancia": concordancia}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    parser.add_argument("--saida", default="resultados/rq07")
    args = parser.parse_args(argv)

    resultado = gerar(args.entrada, args.saida)
    for c in resultado["concordancia"]:
        if c["dimensao"] == "Geral":
            print(f"{c['par']}: {fmt((c['pct_mudaram'] or 0) * 100, 1)}% mudaram de categoria, "
                  f"kappa ponderado = {fmt(c['kappa'], 3)} (n = {c['n']})")
    print(f"Tabelas e figuras salvas em {args.saida}/")


if __name__ == "__main__":
    main()
