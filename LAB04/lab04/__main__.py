"""Ponto de entrada único do projeto: `python -m lab04`.

As etapas do estudo (simulação, testes e dashboard) serão chamadas a partir daqui.
"""

from lab04.config import ALFA, N_SIMULACOES, SEMENTE


def main() -> None:
    print(f"LAB04 | semente={SEMENTE} | alfa={ALFA} | simulações={N_SIMULACOES}")


if __name__ == "__main__":
    main()
