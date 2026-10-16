# LAB03 — Divisão de tarefas da Sprint 2 (Lab03S02)

Baseada na divisão sugerida pelo enunciado (seção 10) e na continuidade dos papéis
de cada integrante na Sprint 1 (visível no histórico de commits do repositório):

- **A — PedroL10**: seleção de repositórios, funil e metadados (S01).
- **B — EnricoBessa**: coleta de releases/commits e lead time (S01).
- **C — bitpickle (Péricles Pires)**: workflow runs, cache/rate limit, CFR(a) e tempo de recuperação (S01).

Critério de divisão: tarefas em volume e dificuldade comparáveis entre os três, cada
uma rastreável por pelo menos uma Issue com código commitado (regra da seção 10 —
sem isso, a nota individual da sprint é zerada).

## Tarefa comum aos três (mesmo esforço para todos)

- **Amostra-ouro:** rotular, cada um de forma independente — sem consultar os
  demais nem ver a saída da heurística automática —, os 60 repositórios sorteados
  com semente fixa (`random_state=42`):
  - tipo do projeto (biblioteca/framework, aplicação/serviço, ferramenta CLI, outro);
  - se as releases representam entregas reais ao usuário (sim/não/incerto);
  - para 5 releases sorteadas de cada repositório: se é corretiva (sim/não).
  - Cada um abre sua própria Issue e commita sua própria planilha de rótulos.
  - Prazo combinado entre os três antes de seguir para o consenso.

## A — PedroL10

1. Ampliar a amostra de 100 para **≥ 300 repositórios** (ajustar `config.yaml`,
   rodar o pipeline, atualizar o funil de seleção em `resultados/`).
2. Depois que as 3 planilhas de rótulos estiverem prontas: calcular a
   **concordância entre avaliadores** (kappa de Fleiss) nas três dimensões
   rotuladas, e conduzir a consolidação do **rótulo de consenso** (registrando o
   protocolo de desempate usado).
3. Artigo: seção de metodologia — funil de seleção e protocolo de validação manual.

## B — EnricoBessa (você)

1. Rotulagem independente da amostra-ouro (tarefa comum acima).
2. Implementar em `metricas/` a **heurística de release corretiva** (CFR
   variante b): patch-only no SemVer e/ou commits com `revert`/`hotfix`/`fix`
   entre releases — com testes e fixtures, cobertura ≥ 80%.
3. Depois que o consenso (de A) estiver pronto: **avaliar a heurística** com
   precisão/recall/F1 (`precision_recall_fscore_support`) contra o consenso;
   refinar até F1 ≥ 0,70 (ou documentar por que não), registrando as versões
   testadas.
4. Artigo: trecho de metodologia sobre a definição operacional de release
   corretiva e sua validação.

## C — bitpickle (Péricles Pires)

1. Rotulagem independente da amostra-ouro (tarefa comum acima).
2. Consolidar a **coleta completa** da amostra ampliada (releases, commits,
   workflow runs) para os ≥ 300 repositórios definidos por A.
3. Gerar o **dataset final em .csv com dicionário de dados** (nome, tipo,
   unidade e fórmula/origem de cada coluna).
4. Artigo: trecho de metodologia sobre fonte de dados e dicionário de dados.

## Observações

- Nenhuma tarefa de código conta sem commit referenciando o número da Issue
  (`git commit -m "#NUMERO ..."`).
- A tarefa de B (heurística CFR b) depende do consenso de A; combinar prazos
  para não bloquear a sprint.
- A tarefa de C (dataset final) depende da amostra ampliada de A.
