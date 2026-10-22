"""Funcoes comuns aos scripts de analise: leitura do dataset, tabelas e estilo dos graficos."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera arquivos sem precisar de tela

# Paleta (referencia do skill de dataviz): azul e laranja para variantes a/b;
# rampa ordinal de azul, escura -> clara, para Elite -> Low.
COR_A, COR_B = "#2a78d6", "#eb6834"
CORES_CATEGORIA = {"Elite": "#104281", "High": "#256abf", "Medium": "#5598e7", "Low": "#86b6ef"}
TEXTO, TEXTO_SECUNDARIO, GRADE, SUPERFICIE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"


def float_ou_none(valor) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def inteiro(valor) -> int:
    return int(float(valor)) if valor not in (None, "") else 0


def carregar(caminho: str | Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def fmt(valor, casas: int = 2) -> str:
    """Numero com virgula decimal (para as tabelas do artigo); '-' se ausente."""
    if valor is None:
        return "-"
    if isinstance(valor, bool):
        return "sim" if valor else "nao"
    if isinstance(valor, int):
        return str(valor)
    return f"{valor:.{casas}f}".replace(".", ",")


def fmt_p(valor) -> str:
    """p-valor: notacao '< 0,001' para valores muito pequenos."""
    if valor is None:
        return "-"
    return "< 0,001" if valor < 0.001 else fmt(valor, 3)


def markdown(cabecalho: list[str], linhas: list[list[str]]) -> str:
    texto = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join("---" for _ in cabecalho) + " |"]
    texto += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return "\n".join(texto) + "\n"


def salvar_csv(linhas: list[dict], caminho: Path) -> None:
    campos: list[str] = []
    for linha in linhas:
        campos += [c for c in linha if c not in campos]
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def estilo_eixo(ax) -> None:
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRADE)
    ax.tick_params(colors=TEXTO_SECUNDARIO, labelsize=8)
    ax.yaxis.grid(True, color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)
