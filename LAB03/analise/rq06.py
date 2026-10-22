"""RQ 06 - caracteristicas dos repositorios associadas ao desempenho DORA.

Le o CSV final da amostra e compara as metricas DORA (RQ 01 a RQ 04) entre
subgrupos de repositorios, para os fatores: linguagem principal, popularidade
(quartis de estrelas), numero de contribuidores (quartis) e idade do
repositorio (quartis). Linguagens com menos de `MIN_POR_LINGUAGEM`
repositorios sao juntadas em "Outras", para nao fragmentar o teste.

O fator "tipo do projeto" so existe para os repositorios rotulados na
amostra-ouro (secao 6); ele entra quando o arquivo de rotulos e passado em
`--rotulos` e e testado so sobre esses repositorios.

Todos os p-valores (fator x metrica) sao corrigidos juntos pelo metodo de Holm.

Grava em `resultados/rq06/`:
- `testes.md` / `.csv`: teste, n, estatistica, p-valor, p corrigido, tamanho de
  efeito e sua interpretacao, por fator x metrica;
- `medianas.md`: n e mediana de cada metrica em cada grupo, para dizer *qual*
  grupo vai melhor quando a diferenca e significativa;
- `figuras/efeitos.png`: tamanho de efeito por fator x metrica, com os significativos marcados.

Uso:
    python -m analise.rq06 --entrada resultados/amostra_metricas.csv [--rotulos resultados/amostra_ouro_pedro.csv]

O CSV de entrada precisa ter, por repositorio, as colunas:
    language, stargazers_count, n_contribuidores, idade_dias   (fatores)
    deployment_frequency, cfr_ci, lead_time_release_dias,
    tempo_recuperacao_horas                                   (metricas DORA)
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from analise.comum import (
    SUPERFICIE,
    TEXTO,
    TEXTO_SECUNDARIO,
    carregar,
    fmt,
    fmt_p,
    markdown,
    salvar_csv,
)
from metricas.subgrupos import agrupar_por_grupo, agrupar_raros, comparar_grupos, corrigir_holm, quartis

import matplotlib.pyplot as plt  # noqa: E402  (depois de analise.comum, que escolhe o backend)
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

METRICAS = {
    "deployment_frequency": "deployment_frequency",
    "cfr": "cfr_ci",
    "lead_time": "lead_time_release_dias",
    "tempo_recuperacao": "tempo_recuperacao_horas",
}

ROTULOS_METRICA = {
    "deployment_frequency": "Deployment frequency",
    "cfr": "CFR (a)",
    "lead_time": "Lead time (a)",
    "tempo_recuperacao": "Tempo de recuperação",
}

FATORES_NUMERICOS = {
    "popularidade": "stargazers_count",
    "contribuidores": "n_contribuidores",
    "idade": "idade_dias",
}

ROTULOS_FATOR = {
    "linguagem": "Linguagem",
    "popularidade": "Popularidade (quartis de estrelas)",
    "contribuidores": "Contribuidores (quartis)",
    "idade": "Idade (quartis)",
    "tipo_projeto": "Tipo do projeto (amostra-ouro)",
}

MIN_POR_LINGUAGEM = 10

# Rampa sequencial de azul (referencia do skill de dataviz), clara -> escura.
RAMPA_EFEITO = LinearSegmentedColormap.from_list("efeito", ["#f0f6fe", "#9ec5f4", "#3987e5", "#1c5cab", "#0d366b"])


def _float_ou_none(valor: str | None) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def carregar_repositorios(caminho_csv: str) -> list[dict]:
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def carregar_tipos(caminho_rotulos: str | Path) -> dict[str, str]:
    """`full_name -> tipo_projeto` da planilha de rotulos (primeiro valor preenchido por repositorio)."""
    tipos: dict[str, str] = {}
    for linha in carregar(caminho_rotulos):
        tipo = (linha.get("tipo_projeto") or "").strip()
        if tipo and linha["full_name"] not in tipos:
            tipos[linha["full_name"]] = tipo
    return tipos


def _grupos_do_fator(repositorios: list[dict], fator: str) -> list:
    if fator == "linguagem":
        return agrupar_raros([linha.get("language") for linha in repositorios], MIN_POR_LINGUAGEM)
    if fator == "tipo_projeto":
        return [linha.get("tipo_projeto") or None for linha in repositorios]

    coluna = FATORES_NUMERICOS[fator]
    valores = [_float_ou_none(linha.get(coluna)) for linha in repositorios]
    # quartis() exige lista sem None: repos sem o fator ficam de fora do agrupamento
    indices_validos = [i for i, v in enumerate(valores) if v is not None]
    grupos_validos = quartis([valores[i] for i in indices_validos])
    grupos: list = [None] * len(valores)
    for posicao, indice in enumerate(indices_validos):
        grupos[indice] = f"Q{grupos_validos[posicao]}"
    return grupos


def _fatores(repositorios: list[dict]) -> list[str]:
    fatores = ["linguagem", "popularidade", "contribuidores", "idade"]
    if any(linha.get("tipo_projeto") for linha in repositorios):
        fatores.append("tipo_projeto")
    return fatores


def calcular_rq06(repositorios: list[dict]) -> list[dict]:
    """Um resultado por combinacao fator x metrica, ja com p-valor corrigido (Holm)."""
    resultados = []

    for fator in _fatores(repositorios):
        grupos_do_fator = _grupos_do_fator(repositorios, fator)
        for nome_metrica, coluna_metrica in METRICAS.items():
            valores_metrica = [_float_ou_none(linha.get(coluna_metrica)) for linha in repositorios]
            # Repositorio sem grupo (ex.: sem rotulo de tipo) fica fora do teste.
            grupos = agrupar_por_grupo(
                [v if g is not None else None for v, g in zip(valores_metrica, grupos_do_fator)],
                grupos_do_fator,
            )
            comparacao = comparar_grupos(grupos)
            resultados.append(
                {"fator": fator, "metrica": nome_metrica, "n_grupos": len(grupos), **comparacao}
            )

    return corrigir_holm(resultados)


def medianas_por_grupo(repositorios: list[dict]) -> list[dict]:
    linhas = []
    for fator in _fatores(repositorios):
        grupos_do_fator = _grupos_do_fator(repositorios, fator)
        rotulos = sorted({g for g in grupos_do_fator if g is not None}, key=str)
        for rotulo in rotulos:
            membros = [r for r, g in zip(repositorios, grupos_do_fator) if g == rotulo]
            linha = {"fator": fator, "grupo": rotulo, "n": len(membros)}
            for nome, coluna in METRICAS.items():
                valores = [v for r in membros if (v := _float_ou_none(r.get(coluna))) is not None]
                linha[nome] = statistics.median(valores) if valores else None
            linhas.append(linha)
    return linhas


def figura_efeitos(resultados: list[dict], caminho: Path) -> None:
    fatores = list(dict.fromkeys(r["fator"] for r in resultados))
    metricas = list(METRICAS)
    matriz = [[0.0] * len(metricas) for _ in fatores]
    textos = [[""] * len(metricas) for _ in fatores]
    for r in resultados:
        i, j = fatores.index(r["fator"]), metricas.index(r["metrica"])
        if r.get("efeito") is None:
            textos[i][j] = "-"
            continue
        efeito = abs(r["efeito"])
        simbolo = "ε²" if r["teste"] == "kruskal-wallis" else "|δ|"
        matriz[i][j] = efeito
        textos[i][j] = f"{simbolo} = {fmt(efeito)}" + (" *" if r.get("significativo") else "")

    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.7 * len(fatores)), facecolor=SUPERFICIE)
    ax.imshow(matriz, cmap=RAMPA_EFEITO, vmin=0, vmax=max(0.3, max(max(l) for l in matriz)), aspect="auto")
    ax.set_xticks(range(len(metricas)), [ROTULOS_METRICA[m] for m in metricas], fontsize=8.5, color=TEXTO)
    ax.set_yticks(range(len(fatores)), [ROTULOS_FATOR[f] for f in fatores], fontsize=8.5, color=TEXTO)
    ax.tick_params(length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    # Linhas brancas entre as celulas.
    ax.set_xticks([x - 0.5 for x in range(1, len(metricas))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(fatores))], minor=True)
    ax.grid(which="minor", color=SUPERFICIE, linewidth=3)
    ax.tick_params(which="minor", length=0)
    limite_escuro = 0.6 * max(0.3, max(max(l) for l in matriz))
    for i, linha in enumerate(textos):
        for j, texto in enumerate(linha):
            ax.text(j, i, texto, ha="center", va="center", fontsize=8,
                    color="#ffffff" if matriz[i][j] > limite_escuro else TEXTO)
    ax.set_title("RQ 06 - Tamanho de efeito por fator e métrica", fontsize=11, color=TEXTO, loc="left")
    fig.text(0.01, 0.01, "* significativo a 5% após a correção de Holm. ε²: Kruskal-Wallis; |δ|: Cliff (2 grupos).",
             fontsize=7.5, color=TEXTO_SECUNDARIO)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def gerar(entrada: str | Path, saida: str | Path, rotulos: str | Path | None = None) -> list[dict]:
    repositorios = carregar_repositorios(str(entrada))
    if rotulos:
        tipos = carregar_tipos(rotulos)
        for linha in repositorios:
            linha["tipo_projeto"] = tipos.get(linha["full_name"])

    resultados = calcular_rq06(repositorios)
    saida = Path(saida)
    (saida / "figuras").mkdir(parents=True, exist_ok=True)

    salvar_csv(resultados, saida / "testes.csv")
    (saida / "testes.md").write_text(
        f"# RQ 06 - Comparacao entre subgrupos ({len(resultados)} testes, correcao de Holm)\n\n"
        "Efeito: epsilon ao quadrado (Kruskal-Wallis; < 0,01 desprezivel, < 0,08 pequeno, "
        "< 0,26 medio, >= 0,26 grande) ou Cliff's delta (Mann-Whitney; Romano et al., 2006).\n\n"
        + markdown(
            ["Fator", "Metrica", "Teste", "Grupos", "n", "Estatistica", "p", "p (Holm)", "Efeito", "Magnitude", "Signif."],
            [[ROTULOS_FATOR[r["fator"]], ROTULOS_METRICA[r["metrica"]], r["teste"] or "-", str(r["n_grupos"]),
              str(r["n"]), fmt(r["estatistica"]), fmt_p(r["p_valor"]), fmt_p(r.get("p_valor_corrigido")),
              fmt(r["efeito"], 3), r.get("interpretacao_efeito") or "-",
              "sim" if r.get("significativo") else "nao"] for r in resultados],
        ),
        encoding="utf-8",
    )

    medianas = medianas_por_grupo(repositorios)
    (saida / "medianas.md").write_text(
        "# RQ 06 - Mediana de cada metrica por grupo\n\n"
        + markdown(
            ["Fator", "Grupo", "n", *ROTULOS_METRICA.values()],
            [[ROTULOS_FATOR[m["fator"]], str(m["grupo"]), str(m["n"]), *[fmt(m[k]) for k in METRICAS]]
             for m in medianas],
        ),
        encoding="utf-8",
    )
    figura_efeitos(resultados, saida / "figuras" / "efeitos.png")
    return resultados


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--entrada", default="resultados/amostra_metricas.csv")
    parser.add_argument("--saida", default="resultados/rq06")
    parser.add_argument("--rotulos", default=None, help="Planilha da amostra-ouro com a coluna tipo_projeto")
    args = parser.parse_args(argv)

    for resultado in gerar(args.entrada, args.saida, args.rotulos):
        print(
            f"{resultado['fator']} x {resultado['metrica']}: "
            f"{resultado['teste']} p_corrigido={resultado.get('p_valor_corrigido')} "
            f"efeito={resultado.get('efeito')} significativo={resultado.get('significativo')}"
        )
    print(f"Tabelas e figura salvas em {args.saida}/")


if __name__ == "__main__":
    main()
