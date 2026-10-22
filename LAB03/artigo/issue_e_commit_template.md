## Issue 1 — heurística de CFR (b)

**Título:** `[Lab03S02] Heurística de release corretiva e CFR (b)`

**Descrição:**
```
Implementa a heurística de release corretiva (patch-only no SemVer e/ou
palavra-chave revert/hotfix/fix nas mensagens de commit) e o cálculo de CFR
variante (b) por repositório, com censura dos últimos 7 dias da janela.

Avalia a heurística (precisão/recall/F1) contra o consenso da amostra-ouro
(depende da Issue de validação manual).

Arquivos: metricas/cfr.py, tests/test_cfr.py, pipeline/commits.py (campos
tag_anterior/mensagens_commits), pipeline/__main__.py (dados/cfr.csv).
```

**Assignee:** EnricoBessa

---

## Issue 2 — rotulagem da amostra-ouro

**Título:** `[Lab03S02] Rotulagem independente da amostra-ouro — Enrico`

**Descrição:**
```
Rotula, de forma independente (sem consultar os demais integrantes nem a
saída da heurística automática), os 60 repositórios sorteados com seed fixa:
tipo do projeto, se as releases representam entrega real, e se cada uma de
5 releases sorteadas por repositório é corretiva.

Planilha gerada por pipeline/amostra_ouro.py, preenchida manualmente.
```

**Assignee:** EnricoBessa

---

## Mensagens de commit

Depois de rodar os testes localmente (`python -m pytest --cov=metricas --cov-fail-under=80`)
e confirmar que está tudo verde:

```powershell
git add metricas/cfr.py tests/test_cfr.py pipeline/commits.py tests/test_commits.py pipeline/__main__.py
git status
git commit -m "#5 Implementa heuristica e calculo de CFR variante b (RQ03)"
```

```powershell
git add pipeline/amostra_ouro.py tests/test_amostra_ouro.py
git commit -m "#5 Gera planilha da amostra-ouro com sorteio reproduzivel"
```

```powershell
git add resultados/amostra_ouro_enrico.csv
git commit -m "#6 Rotulagem independente da amostra-ouro"
```

```powershell
git pull origin master
git push origin master
```

Depois: conferir a aba **Actions** (workflow `lab03-testes` verde), comentar nas
duas Issues com a evidência (saída do pytest, link do CI), mover os cartões
para "Done" e fechar.


