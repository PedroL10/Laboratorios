"""RQ 05 - correlacao entre deployment frequency e change failure rate.

Le o CSV final da amostra (RQ 01 a RQ 04 ja calculadas por repositorio) e
reporta a correlacao de Spearman entre deployment frequency e CFR, separada
para as duas variantes do CFR (a: proxy de CI, b: proxy de entrega).

Grava em `resultados/rq05/`:
- `spearman.md` / `.csv`: rho, p-valor, n e forca da correlacao por variante;
- `figuras/dispersao.png`: frequencia (eixo x em escala log) x CFR, um painel por variante.

Uso:
    python -m analise.rq05 --entrada resultados/amostra_metricas.csv

O CSV de entrada precisa ter, por repositorio, as colunas:
    deployment_frequency  (RQ 01, releases por semana)
    cfr_ci                (RQ 03 variante a, proxy de CI)
    cfr_entrega           (RQ 03 variante b, proxy de entrega)
Repositorios sem um desses valores sao ignorados em cada correlacao
(ver `metricas.correlacao.spearman_frequencia_cfr`).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analise.comum import (
    COR_A,
    COR_B,
    SUPERFICIE,
    TEXTO,
    TEXTO_SECUNDARIO,
    GRADE,
    estilo_eixo,
    fmt,
    fmt_p,
    markdown,
    salvar_csv,
)
from metricas.correlacao import interpretar_rho, spearman_frequencia_cfr

import matplotlib.pyplot as plt  # noqa: E402  (depois de analise.comum, que escolhe o backend)

VARIANTES_CFR = {"a": "cfr_ci", "b": "cfr_entrega"}
ROTULOS_VARIANTE = {"a": "CFR (a) proxy de CI", "b": "CFR (b) proxy de entrega"}


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def carregar_repositorios(caminho_csv: str) -> list[dict]:
    """Le o CSV final e devolve os campos numericos usados pela RQ 05."""
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return [
            {
                "full_name": linha.get("full_name"),
                "deployment_frequency": _float_ou_none(linha.get("deployment_frequency")),
                "cfr_ci": _float_ou_none(linha.get("cfr_ci")),
                "cfr_entrega": _float_ou_none(linha.get("cfr_entrega")),
            }
            for linha in leitor
        ]


def calcular_rq05(repositorios: list[dict]) -> dict:
    """Correlacao de Spearman entre deployment frequency e CFR, nas 2 variantes."""
    return {
        letra: spearman_frequencia_cfr(repositorios, chave_cfr=chave)
        for letra, chave in VARIANTES_CFR.items()
    }


def figura_dispersao(repositorios: list[dict], resultado: dict, caminho: Path) -> None:
    fig, eixos = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=SUPERFICIE, sharey=True)
    for ax, (letra, chave), cor in zip(eixos, VARIANTES_CFR.items(), (COR_A, COR_B)):
        estilo_eixo(ax)
        ax.xaxis.grid(True, color=GRADE, linewidth=0.6)
        pares = [
            (r["deployment_frequency"], r[chave])
            for r in repositorios
            if r["deployment_frequency"] and r[chave] is not None
        ]
        if pares:
            x, y = zip(*pares)
            ax.scatter(x, y, s=22, color=cor, alpha=0.6, edgecolors=SUPERFICIE, linewidths=0.6)
            ax.set_xscale("log")
        valores = resultado[letra]
        ax.set_title(ROTULOS_VARIANTE[letra], fontsize=10, color=TEXTO, loc="left")
        ax.text(
            0.98, 0.96,
            f"ρ = {fmt(valores['rho'])}  (p {fmt_p(valores['p_valor'])}, n = {valores['n']})",
            transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=TEXTO,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": SUPERFICIE, "edgecolor": GRADE},
        )
        ax.set_xlabel("Deployment frequency (releases/semana, log)", fontsize=8, color=TEXTO_SECUNDARIO)
    eixos[0].set_ylabel("Change failure rate (proporção)", fontsize=8, color=TEXTO_SECUNDARIO)
    fig.suptitle("RQ 05 - Frequência de deploy x taxa de falha (Spearman)", fontsize=11,
                 color=TEXTO, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def gerar(entrada: str | Path, saida: str | Path) -> dict:
    repositorios = carregar_repositorios(str(entrada))
    resultado = calcular_rq05(repositorios)
    saida = Path(saida)
    (saida / "figuras").mkdir(parents=True, exist_ok=True)

    linhas = [
        {"variante": ROTULOS_VARIANTE[letra], **valores, "forca": interpretar_rho(valores["rho"])}
        for letra, valores in resultado.items()
    ]
    salvar_csv(linhas, saida / "spearman.csv")
    (saida / "spearman.md").write_text(
        "# RQ 05 - Spearman entre deployment frequency e CFR\n\n"
        "Forca pelo modulo de rho (Cohen, 1988): < 0,1 desprezivel; < 0,3 fraca; "
        "< 0,5 moderada; >= 0,5 forte. Correlacao nao implica causalidade.\n\n"
        + markdown(
            ["Variante do CFR", "rho", "p-valor", "n", "Forca"],
            [[l["variante"], fmt(l["rho"], 3), fmt_p(l["p_valor"]), str(l["n"]), l["forca"] or "-"] for l in linhas],
        ),
        encoding="utf-8",
    )
    figura_dispersao(repositorios, resultado, saida / "figuras" / "dispersao.png")
    return resultado


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    parser.add_argument("--saida", default="resultados/rq05")
    args = parser.parse_args(argv)

    resultado = gerar(args.entrada, args.saida)
    for letra, valores in resultado.items():
        print(f"CFR variante ({letra}): rho={valores['rho']} p={valores['p_valor']} n={valores['n']}")
    print(f"Tabela e figura salvas em {args.saida}/")


if __name__ == "__main__":
    main()
