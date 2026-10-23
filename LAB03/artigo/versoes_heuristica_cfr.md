# Versões testadas da heurística de release corretiva (CFR b)

Precisão, recall e F1 de cada versão frente aos rótulos da amostra-ouro (100 releases
de 20 repositórios; 47 corretivas pela referência), calculados por
`python -m analise.amostra_ouro` (relatório em `resultados/amostra_ouro/validacao.md`).
Rótulos produzidos por IA (Claude), com autorização do professor — ver metodologia.

| Versão | Regra | Releases marcadas | Precisão | Recall | F1 |
| --- | --- | ---: | --- | --- | --- |
| v1 | Patch-only no SemVer **OU** algum commit com `fix`/`revert`/`hotfix` no título | 93 | 0,49 | 0,98 | 0,66 |
| — | Só patch-only no SemVer | – | 0,64 | 0,64 | 0,64 |
| — | Só maioria (≥ 50%) dos commits com a palavra-chave | – | 0,67 | 0,26 | 0,37 |
| **v2 (final)** | Patch-only no SemVer **OU** maioria (≥ 50%) dos commits com a palavra-chave (palavra inteira) | 52 | 0,62 | 0,68 | 0,65 |

Intervalo de 95% (bootstrap) da v2: precisão 0,49–0,75; recall 0,55–0,80; F1 0,53–0,75.

## Versão final usada no artigo

**v2.** Nenhuma versão baseada apenas no número da versão e nos títulos dos commits atingiu
F1 ≥ 0,70. A v1 tinha F1 parecido, mas marcava 93 de 100 releases como corretivas
(precisão 0,49): quase toda release tem ao menos um commit de correção, o que inflava o
CFR (b). A v2 equilibra precisão e recall, distribuindo os erros dos dois lados, e por isso
enviesa menos a estimativa do CFR (b) e do rework rate.

O sinal mais forte observado na rotulagem estava nas *release notes* (seções "Bug Fixes",
"patch release", "hotfix", "regression"), que o pipeline não coleta. Uma heurística que use
as notas é o refinamento natural (trabalho futuro). As variantes foram comparadas na própria
amostra-ouro, sem conjunto separado de teste, o que pode superestimar levemente o
desempenho da v2.
