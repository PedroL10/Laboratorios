"""RQ 08 (bonus) - deployment rework rate, comparado ao CFR (b).

Rework rate = releases corretivas / releases (metrica acrescentada pelo DORA em
2024). Usa a mesma heuristica de release corretiva do CFR (b), mas mede outra
coisa: o CFR (b) olha a release que *falhou* (seguida por uma correcao em ate
7 dias); o rework rate conta as releases que *sao* correcoes, sem limite de
tempo e sem censura.

Grava em `resultados/rq08/rework.md`: mediana e IQR das duas metricas, a
diferenca por repositorio e a correlacao de Spearman entre elas.

Uso:
    python -m analise.rq08 --entrada resultados/amostra_metricas.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scipy.stats import spearmanr

from analise.comum import carregar, float_ou_none, fmt, fmt_p, markdown
from metricas.correlacao import interpretar_rho
from metricas.descritiva import resumo


def calcular_rq08(repositorios: list[dict]) -> dict:
    rework = [float_ou_none(r.get("rework_rate")) for r in repositorios]
    cfr = [float_ou_none(r.get("cfr_entrega")) for r in repositorios]
    pares = [(w, c) for w, c in zip(rework, cfr) if w is not None and c is not None]

    rho = p_valor = None
    if len(pares) >= 2 and len({w for w, _ in pares}) > 1 and len({c for _, c in pares}) > 1:
        resultado = spearmanr([w for w, _ in pares], [c for _, c in pares])
        rho, p_valor = float(resultado.statistic), float(resultado.pvalue)

    return {
        "rework": resumo(rework),
        "cfr_entrega": resumo(cfr),
        "diferenca": resumo([w - c for w, c in pares]),
        "rework_maior": sum(1 for w, c in pares if w > c),
        "n_pares": len(pares),
        "rho": rho,
        "p_valor": p_valor,
    }


def gerar(entrada: str | Path, saida: str | Path) -> dict:
    resultado = calcular_rq08(carregar(entrada))
    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)

    linhas = [
        [nome, str(r["n"]), fmt(r["mediana"], 3), fmt(r["q1"], 3), fmt(r["q3"], 3), fmt(r["iqr"], 3)]
        for nome, r in [
            ("Rework rate", resultado["rework"]),
            ("CFR (b) proxy de entrega", resultado["cfr_entrega"]),
            ("Rework rate - CFR (b), por repositorio", resultado["diferenca"]),
        ]
    ]
    (saida / "rework.md").write_text(
        "# RQ 08 (bonus) - Deployment rework rate x CFR (b)\n\n"
        + markdown(["Metrica", "n", "Mediana", "Q1", "Q3", "IQR"], linhas)
        + f"\nRepositorios com rework rate maior que o CFR (b): {resultado['rework_maior']} "
        f"de {resultado['n_pares']}.\n\n"
        f"Spearman entre rework rate e CFR (b): rho = {fmt(resultado['rho'], 3)}, "
        f"p {fmt_p(resultado['p_valor'])}, n = {resultado['n_pares']} "
        f"({interpretar_rho(resultado['rho']) or '-'}).\n",
        encoding="utf-8",
    )
    return resultado


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    parser.add_argument("--saida", default="resultados/rq08")
    args = parser.parse_args(argv)

    resultado = gerar(args.entrada, args.saida)
    print(f"Rework rate: mediana={fmt(resultado['rework']['mediana'], 3)}; "
          f"CFR (b): mediana={fmt(resultado['cfr_entrega']['mediana'], 3)}; rho={fmt(resultado['rho'], 3)}")
    print(f"Tabela salva em {args.saida}/rework.md")


if __name__ == "__main__":
    main()
