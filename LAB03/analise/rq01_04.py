"""RQ 01 a 04 - estatistica descritiva e classificacao DORA de referencia (C1).

Le o dataset final e grava em `resultados/rq01_04/`:

- `descritiva.csv` / `.md`: n, mediana, Q1, Q3, IQR, minimo e maximo de cada
  metrica (frequencia; lead time a e b; CFR a e b; tempo de recuperacao);
- `censura.md`: casos censurados e dados ignorados (episodios de falha sem
  recuperacao na janela, releases fora do CFR b, compares 404, dias no teto de runs);
- `classificacao_c1.csv` / `.md`: quantos repositorios em cada categoria DORA
  (Elite/High/Medium/Low), por metrica e na classificacao geral;
- `figuras/distribuicoes.png`: boxplots das metricas, com os cortes da tabela DORA;
- `figuras/classificacao_c1.png`: distribuicao das categorias DORA.

Uso (de dentro de LAB03):
    python -m analise.rq01_04 --entrada resultados/amostra_metricas.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera arquivos sem precisar de tela
import matplotlib.pyplot as plt  # noqa: E402

from metricas.classificacao import UMA_POR_MES_EM_SEMANAS  # noqa: E402
from metricas.descritiva import CATEGORIAS, distribuicao_categorias, resumo  # noqa: E402

# (coluna, rotulo, unidade, RQ)
METRICAS = [
    ("deployment_frequency", "Deployment frequency", "releases/semana", "RQ 01"),
    ("lead_time_release_dias", "Lead time (a) por release", "dias", "RQ 02"),
    ("lead_time_commit_dias", "Lead time (b) por commit", "dias", "RQ 02"),
    ("cfr_ci", "CFR (a) proxy de CI", "proporcao", "RQ 03"),
    ("cfr_entrega", "CFR (b) proxy de entrega", "proporcao", "RQ 03"),
    ("tempo_recuperacao_horas", "Tempo de recuperacao", "horas", "RQ 04"),
]

CATEGORIAS_C1 = [
    ("categoria_frequencia", "Deployment frequency"),
    ("categoria_lead_time", "Lead time (a)"),
    ("categoria_cfr", "CFR (a)"),
    ("categoria_recuperacao", "Tempo de recuperação"),
    ("categoria_geral", "Geral (C1)"),
]

# Paleta (referencia do skill de dataviz): azul e laranja para variantes a/b;
# rampa ordinal de azul, escura -> clara, para Elite -> Low.
COR_A, COR_B = "#2a78d6", "#eb6834"
CORES_CATEGORIA = {"Elite": "#104281", "High": "#256abf", "Medium": "#5598e7", "Low": "#86b6ef"}
TEXTO, TEXTO_SECUNDARIO, GRADE, SUPERFICIE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"

# Cortes da tabela DORA, desenhados nos boxplots: (valor, categorias que ele separa).
CORTES = {
    "deployment_frequency": [(7, "Elite / High"), (1, "High / Medium"), (UMA_POR_MES_EM_SEMANAS, "Medium / Low")],
    "lead_time": [(1, "Elite / High"), (7, "High / Medium"), (30, "Medium / Low")],
    "cfr": [(0.15, "Elite / High"), (0.30, "High / Medium"), (0.45, "Medium / Low")],
    "tempo_recuperacao_horas": [(1, "Elite / High"), (24, "High / Medium"), (168, "Medium / Low")],
}


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _inteiro(valor: str | None) -> int:
    return int(float(valor)) if valor not in (None, "") else 0


def carregar(caminho: str | Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def _fmt(valor, casas: int = 2) -> str:
    if valor is None:
        return "-"
    if isinstance(valor, int):
        return str(valor)
    return f"{valor:.{casas}f}".replace(".", ",")


def tabela_descritiva(repositorios: list[dict]) -> list[dict]:
    linhas = []
    for coluna, rotulo, unidade, rq in METRICAS:
        estatisticas = resumo([_float_ou_none(r.get(coluna)) for r in repositorios])
        linhas.append({"rq": rq, "metrica": rotulo, "coluna": coluna, "unidade": unidade, **estatisticas})
    return linhas


def tabela_censura(repositorios: list[dict]) -> list[tuple[str, str]]:
    """Indicadores de censura e de dados ignorados, para a metodologia e as ameacas."""
    n = len(repositorios)
    episodios = sum(_inteiro(r.get("n_episodios")) for r in repositorios)
    censurados = sum(_inteiro(r.get("n_episodios_censurados")) for r in repositorios)
    proporcoes = [_float_ou_none(r.get("proporcao_censurados")) for r in repositorios]
    total_episodios = episodios + censurados

    def contar(condicao) -> int:
        return sum(1 for r in repositorios if condicao(r))

    return [
        ("Repositorios no dataset", str(n)),
        ("Episodios de falha encerrados (RQ 04)", str(episodios)),
        ("Episodios censurados - sem recuperacao ate o fim da janela", str(censurados)),
        (
            "Proporcao de episodios censurados (todos os repositorios)",
            _fmt(censurados / total_episodios if total_episodios else None, 3),
        ),
        ("Mediana, por repositorio, da proporcao de episodios censurados", _fmt(resumo(proporcoes)["mediana"], 3)),
        ("Workflows que ja comecam a janela falhando (inicio desconhecido)",
         str(sum(_inteiro(r.get("n_episodios_sem_inicio")) for r in repositorios))),
        ("Repositorios sem tempo de recuperacao (nenhum episodio encerrado)",
         str(contar(lambda r: _float_ou_none(r.get("tempo_recuperacao_horas")) is None))),
        ("Releases censuradas no CFR (b) - ultimos 7 dias da janela",
         str(sum(_inteiro(r.get("n_releases_censuradas")) for r in repositorios))),
        ("Releases ignoradas no lead time - compare 404 (tag apagada ou reescrita)",
         str(sum(_inteiro(r.get("n_ignoradas_compare_404")) for r in repositorios))),
        ("Repositorios cuja primeira release da historia esta na janela",
         str(sum(_inteiro(r.get("n_ignoradas_primeira_release")) for r in repositorios))),
        ("Repositorios com algum dia acima de 1.000 runs (runs incompletos)",
         str(contar(lambda r: _inteiro(r.get("fatias_no_teto")) > 0))),
    ]


def tabela_classificacao(repositorios: list[dict]) -> list[dict]:
    linhas = []
    for coluna, rotulo in CATEGORIAS_C1:
        dist = distribuicao_categorias([r.get(coluna) or None for r in repositorios])
        linha = {"metrica": rotulo}
        for categoria in CATEGORIAS:
            linha[f"{categoria}_n"] = dist["contagem"][categoria]
            linha[f"{categoria}_pct"] = dist["proporcao"][categoria]
        linha["sem_categoria"] = dist["sem_categoria"]
        linhas.append(linha)
    return linhas


def _markdown(cabecalho: list[str], linhas: list[list[str]]) -> str:
    texto = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join("---" for _ in cabecalho) + " |"]
    texto += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return "\n".join(texto) + "\n"


def _salvar_csv(linhas: list[dict], caminho: Path) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def _estilo_eixo(ax) -> None:
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRADE)
    ax.tick_params(colors=TEXTO_SECUNDARIO, labelsize=8)
    ax.yaxis.grid(True, color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)


def _boxplot(ax, series: list[list[float]], rotulos: list[str], cores: list[str]) -> None:
    caixas = ax.boxplot(
        series,
        tick_labels=rotulos,
        widths=0.5,
        patch_artist=True,
        medianprops={"color": TEXTO, "linewidth": 1.5},
        whiskerprops={"color": TEXTO_SECUNDARIO, "linewidth": 1},
        capprops={"color": TEXTO_SECUNDARIO, "linewidth": 1},
        flierprops={"marker": "o", "markersize": 3, "markeredgewidth": 0, "alpha": 0.5},
    )
    for caixa, voo, cor in zip(caixas["boxes"], caixas["fliers"], cores):
        caixa.set_facecolor(cor + "40")  # preenchimento claro do mesmo tom
        caixa.set_edgecolor(cor)
        caixa.set_linewidth(1.2)
        voo.set_markerfacecolor(cor)


def _cortes(ax, cortes: list[tuple[float, str]]) -> None:
    for valor, rotulo in cortes:
        ax.axhline(valor, color=TEXTO_SECUNDARIO, linewidth=0.8, linestyle=(0, (4, 3)), alpha=0.6)
        ax.annotate(
            rotulo, xy=(1, valor), xycoords=("axes fraction", "data"),
            xytext=(2, 0), textcoords="offset points", va="center", fontsize=7, color=TEXTO_SECUNDARIO,
        )


def _positivos(repositorios: list[dict], coluna: str) -> list[float]:
    """Valores > 0 (a escala logaritmica nao representa zero)."""
    return [v for r in repositorios if (v := _float_ou_none(r.get(coluna))) is not None and v > 0]


def _presentes(repositorios: list[dict], coluna: str) -> list[float]:
    return [v for r in repositorios if (v := _float_ou_none(r.get(coluna))) is not None]


def figura_distribuicoes(repositorios: list[dict], caminho: Path) -> None:
    fig, eixos = plt.subplots(2, 2, figsize=(10, 7.5), facecolor=SUPERFICIE)
    paineis = [
        ("RQ 01 - Deployment frequency (releases/semana, log)",
         [_positivos(repositorios, "deployment_frequency")], ["releases/semana"], [COR_A],
         CORTES["deployment_frequency"], True),
        ("RQ 02 - Lead time (dias, log)",
         [_positivos(repositorios, "lead_time_release_dias"), _positivos(repositorios, "lead_time_commit_dias")],
         ["(a) por release", "(b) por commit"], [COR_A, COR_B], CORTES["lead_time"], True),
        ("RQ 03 - Change failure rate (proporção)",
         [_presentes(repositorios, "cfr_ci"), _presentes(repositorios, "cfr_entrega")],
         ["(a) proxy de CI", "(b) proxy de entrega"], [COR_A, COR_B], CORTES["cfr"], False),
        ("RQ 04 - Tempo de recuperação (horas, log)",
         [_positivos(repositorios, "tempo_recuperacao_horas")], ["horas"], [COR_A],
         CORTES["tempo_recuperacao_horas"], True),
    ]
    for ax, (titulo, series, rotulos, cores, cortes, log) in zip(eixos.flat, paineis):
        _estilo_eixo(ax)
        ax.set_title(titulo, fontsize=10, color=TEXTO, loc="left")
        if not any(series):
            ax.text(0.5, 0.5, "sem dados", ha="center", va="center", color=TEXTO_SECUNDARIO, transform=ax.transAxes)
            continue
        _boxplot(ax, [s or [float("nan")] for s in series], [f"{r}\n(n = {len(s)})" for r, s in zip(rotulos, series)], cores)
        if log:
            ax.set_yscale("log")
        _cortes(ax, cortes)
    fig.suptitle("Distribuição das métricas DORA por repositório", fontsize=12, color=TEXTO, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Linhas tracejadas: cortes entre categorias da tabela de classificação DORA da disciplina.",
             fontsize=7.5, color=TEXTO_SECUNDARIO)
    fig.tight_layout(rect=(0, 0.02, 0.97, 0.97))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def figura_classificacao(classificacao: list[dict], caminho: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 3.6), facecolor=SUPERFICIE)
    _estilo_eixo(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRADE, linewidth=0.6)
    rotulos = [linha["metrica"] for linha in classificacao][::-1]
    linhas = classificacao[::-1]
    esquerda = [0.0] * len(linhas)
    for categoria in CATEGORIAS:
        larguras = [(linha[f"{categoria}_pct"] or 0) * 100 for linha in linhas]
        barras = ax.barh(rotulos, larguras, left=esquerda, color=CORES_CATEGORIA[categoria],
                         edgecolor=SUPERFICIE, linewidth=2, height=0.6, label=categoria)
        for barra, largura, linha in zip(barras, larguras, linhas):
            if largura >= 7:  # rotulo so onde cabe
                cor_texto = "#ffffff" if categoria in ("Elite", "High") else TEXTO
                ax.text(barra.get_x() + largura / 2, barra.get_y() + barra.get_height() / 2,
                        f"{largura:.0f}%", ha="center", va="center", fontsize=7.5, color=cor_texto)
        esquerda = [e + l for e, l in zip(esquerda, larguras)]
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos repositórios classificados", fontsize=8, color=TEXTO_SECUNDARIO)
    ax.legend(ncols=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=8)
    ax.set_title("Classificação DORA de referência (C1)", fontsize=11, color=TEXTO, loc="left", pad=24)
    fig.tight_layout()
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def gerar(entrada: str | Path, saida: str | Path) -> dict:
    repositorios = carregar(entrada)
    saida = Path(saida)
    (saida / "figuras").mkdir(parents=True, exist_ok=True)

    descritiva = tabela_descritiva(repositorios)
    _salvar_csv(descritiva, saida / "descritiva.csv")
    (saida / "descritiva.md").write_text(
        f"# RQ 01 a 04 - estatistica descritiva (n = {len(repositorios)} repositorios)\n\n"
        + _markdown(
            ["RQ", "Metrica", "Unidade", "n", "Mediana", "Q1", "Q3", "IQR", "Min", "Max"],
            [[d["rq"], d["metrica"], d["unidade"], _fmt(d["n"]), _fmt(d["mediana"]), _fmt(d["q1"]),
              _fmt(d["q3"]), _fmt(d["iqr"]), _fmt(d["minimo"]), _fmt(d["maximo"])] for d in descritiva],
        ),
        encoding="utf-8",
    )

    censura = tabela_censura(repositorios)
    (saida / "censura.md").write_text(
        "# Censura e dados ignorados\n\n" + _markdown(["Indicador", "Valor"], [list(c) for c in censura]),
        encoding="utf-8",
    )

    classificacao = tabela_classificacao(repositorios)
    _salvar_csv(classificacao, saida / "classificacao_c1.csv")
    (saida / "classificacao_c1.md").write_text(
        "# Classificacao DORA de referencia (C1: release, lead time a, CFR a)\n\n"
        "Percentual sobre os repositorios com valor para a metrica.\n\n"
        + _markdown(
            ["Metrica", *CATEGORIAS, "Sem valor"],
            [[c["metrica"], *[f"{c[f'{k}_n']} ({_fmt((c[f'{k}_pct'] or 0) * 100, 1)}%)" for k in CATEGORIAS],
              str(c["sem_categoria"])] for c in classificacao],
        ),
        encoding="utf-8",
    )

    figura_distribuicoes(repositorios, saida / "figuras" / "distribuicoes.png")
    figura_classificacao(classificacao, saida / "figuras" / "classificacao_c1.png")
    return {"descritiva": descritiva, "censura": censura, "classificacao": classificacao}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    parser.add_argument("--saida", default="resultados/rq01_04")
    args = parser.parse_args(argv)

    resultado = gerar(args.entrada, args.saida)
    for d in resultado["descritiva"]:
        print(f"{d['rq']} {d['metrica']}: mediana={_fmt(d['mediana'])} IQR={_fmt(d['iqr'])} n={d['n']}")
    print(f"Tabelas e figuras salvas em {args.saida}/")


if __name__ == "__main__":
    main()
