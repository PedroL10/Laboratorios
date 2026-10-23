# Versões testadas da heurística de release corretiva (CFR b)

Precisão, recall e F1 de cada versão frente aos rótulos manuais da amostra-ouro
(seção 6 do enunciado), calculados por `metricas.cfr.avaliar_heuristica`.

| Versão | O que mudou em relação à anterior | Precisão | Recall | F1 | Data |
| --- | --- | --- | --- | --- | --- |
| v1 | Patch-only no SemVer OU palavra-chave (`revert`/`hotfix`/`fix`) na mensagem de commit — `metricas/cfr.py` | [a calcular] | [a calcular] | [a calcular] | – |

## Versão final usada no artigo

[PENDENTE: depende da rotulagem da amostra-ouro. Se o F1 da v1 ficar abaixo de
0,70, refinar a heurística (ex.: buscar `fix` como palavra inteira, já que hoje
ela também casa com `prefix` e `fixture`) e registrar cada nova versão nesta tabela.]
