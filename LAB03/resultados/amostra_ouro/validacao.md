# Validacao manual da heuristica de release corretiva

Avaliador(es): claude. Releases sorteadas: 100; com rotulo de referencia: 100 (47 corretivas); sem referencia (sem rotulo ou empate): 0. Repositorios: 20.

## Desempenho (intervalo de 95% por bootstrap)

| Heuristica | Precisao | Recall | F1 |
| --- | --- | --- | --- |
| v2 (em uso): patch-only OU maioria dos commits corretivos [52 marcadas] | 0,62 (0,49–0,75) | 0,68 (0,55–0,80) | 0,65 (0,53–0,75) |
| v1: patch-only OU algum commit corretivo [93 marcadas] | 0,49 | 0,98 | 0,66 |
| So patch-only no SemVer | 0,64 | 0,64 | 0,64 |
| So maioria dos commits corretivos | 0,67 | 0,26 | 0,37 |


## Matriz de confusao (v2)

|  | Referencia: corretiva | Referencia: nao corretiva |
| --- | --- | --- |
| Heuristica: corretiva | 32 | 20 |
| Heuristica: nao corretiva | 15 | 33 |


## Rotulos por repositorio

| Tipo do projeto | Repositorios |
| --- | --- |
| aplicacao/servico | 8 |
| biblioteca/framework | 6 |
| ferramenta CLI | 5 |
| outro | 1 |


| Releases sao entregas reais? | Repositorios |
| --- | --- |
| sim | 20 |


Um unico avaliador: os rotulos dele sao a referencia e a concordancia entre avaliadores (kappa de Fleiss) nao pode ser calculada.
