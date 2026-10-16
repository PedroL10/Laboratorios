# LAB02S01 - Katas selecionados

## Objetivo

Este documento define os quatro objetos experimentais da Sprint 1. Todos os participantes resolverao os mesmos katas, alternando os tratamentos IA e MANUAL conforme a matriz definida na Issue 3.

Os katas sao autorais e foram desenhados para nao depender de bibliotecas externas. Os dois primeiros sao faceis e os dois ultimos sao medios. A classificacao sera validada em um piloto curto antes da execucao oficial; se algum kata ficar muito acima ou abaixo dos demais, o grupo deve ajustar o enunciado e registrar a decisao.

## Resumo

| ID  | Nome                    | Nivel | Estruturas principais                  | Testes |
| --- | ----------------------- | ----- | -------------------------------------- | -----: |
| K1  | Resumo de leituras      | Facil | lista, media, filtros e arredondamento |     10 |
| K2  | Validador de etiquetas  | Facil | strings, pilha e regras locais         |     11 |
| K3  | Janela de entregas      | Medio | ordenacao, intervalos e agrupamento    |     10 |
| K4  | Pontuacao de campeonato | Medio | dicionarios, regras e desempate        |     10 |

## Regras comuns do experimento

- Linguagem: Python 3.
- Cada kata sera executado em um trial separado de no maximo 35 minutos.
- Os participantes recebem este enunciado e os testes de aceitacao.
- Nao existe solucao de referencia neste repositorio.
- A solucao do participante deve ficar no arquivo `solution.py` dentro da copia do trial, em `LAB02/trials/<participante>/<kata>_<tratamento>/`.
- Os testes devem ser executados com `pytest`.
- O grupo deve registrar a versao do Python e do pytest antes da Sprint 2.

## Controle de dificuldade

Os quatro katas usam listas, strings ou dicionarios, exigem validacao de entradas e possuem dez testes de aceitacao. K1 e K2 sao faceis porque usam uma passagem principal pelos dados e regras locais. K3 e K4 sao medios porque combinam varias regras, estado acumulado e ordenacao ou agrupamento.

A diferenca de nivel deve ser registrada como uma decisao metodologica no relatorio. Para comparacoes agregadas, o grupo deve apresentar tambem os resultados separados por kata ou nivel.
