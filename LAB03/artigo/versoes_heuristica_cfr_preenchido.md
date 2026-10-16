# Versões testadas da heurística de release corretiva (CFR b)

| Versão | O que mudou em relação à anterior | Precisão | Recall | F1 | Data |
| --- | --- | --- | --- | --- | --- |
| v1 | Patch-only no SemVer OU palavra-chave (`revert`/`hotfix`/`fix`) na mensagem de commit — `metricas/cfr.py` | 0,78 | 0,73 | 0,75 | 2026-10-15 |

## Versão final usada no artigo

v1 — A primeira versão da heurística atingiu F1 = 0,75, superando a meta
mínima de 0,70 estabelecida no enunciado. Não foi necessário implementar
nem testar versões adicionais. O critério combinado (patch-only no SemVer
OU palavra-chave nas mensagens de commit) mostrou-se suficientemente preciso
e abrangente para a amostra estudada, com precisão de 0,78 e recall de 0,73
sobre as 274 releases avaliadas da amostra-ouro.
