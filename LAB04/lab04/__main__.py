"""Ponto de entrada único do projeto: `python -m lab04`.

As próximas etapas do estudo (simulação, testes e dashboard) serão chamadas a partir daqui.
"""

from lab04.config import ALFA, N_SIMULACOES, SEMENTE
from lab04.distribuicao import PASTA_RESULTADOS, analisar


def main() -> None:
    print(f"LAB04 | semente={SEMENTE} | alfa={ALFA} | simulações={N_SIMULACOES}")
    analisar()
    print(f"Forma da distribuição salva em {PASTA_RESULTADOS}")


if __name__ == "__main__":
    main()
