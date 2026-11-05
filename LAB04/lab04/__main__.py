"""Ponto de entrada único do projeto: `python -m lab04`.

A próxima etapa do estudo (dashboard) será chamada a partir daqui.
"""

from lab04.config import ALFA, N_SIMULACOES, SEMENTE, criar_rng
from lab04.distribuicao import PASTA_RESULTADOS, analisar
from lab04.testes import comparar_testes


def main() -> None:
    print(f"LAB04 | semente={SEMENTE} | alfa={ALFA} | simulações={N_SIMULACOES}")
    analisar()
    print(f"Forma da distribuição salva em {PASTA_RESULTADOS}")

    _, interpretacoes = comparar_testes(criar_rng())
    for linha in interpretacoes:
        print(linha)


if __name__ == "__main__":
    main()
