"""Ponto de entrada único do projeto: `python -m lab04`.

Roda o estudo do início ao fim e gera o dashboard em dashboard/index.html.
"""

from lab04.config import ALFA, N_SIMULACOES, SEMENTE, criar_rng
from lab04.dashboard import gerar_dashboard
from lab04.distribuicao import PASTA_RESULTADOS, analisar
from lab04.erro_tipo1 import extrair_erro_tipo1
from lab04.poder import calcular_poder
from lab04.testes import comparar_testes


def main() -> None:
    print(f"LAB04 | semente={SEMENTE} | alfa={ALFA} | simulações={N_SIMULACOES}")
    analisar()
    print(f"Forma da distribuição salva em {PASTA_RESULTADOS}")

    _, interpretacoes = comparar_testes(criar_rng())
    for linha in interpretacoes:
        print(linha)

    # Uma única simulação gera o G3 e o G4: o erro tipo I são as linhas com fator 1.
    poder = calcular_poder(criar_rng())
    poder.to_csv(PASTA_RESULTADOS / "poder.csv", index=False, float_format="%.4f")
    erro_tipo1 = extrair_erro_tipo1(poder)
    erro_tipo1.to_csv(PASTA_RESULTADOS / "erro_tipo1.csv", index=False, float_format="%.4f")
    print(erro_tipo1.to_string(index=False))

    print(f"Dashboard gerado em {gerar_dashboard()}")


if __name__ == "__main__":
    main()
