### Change failure rate — variante (b), proxy de entrega

Definimos uma release R como **corretiva** quando pelo menos uma das condições
abaixo é satisfeita em relação à release anterior:

- a versão muda apenas no número de *patch* do Versionamento Semântico
  (ex.: `1.4.3` → `1.4.4`); e/ou
- há commits com `revert`, `hotfix` ou `fix` na mensagem entre as duas releases.

O CFR (b) do repositório é a proporção de releases avaliadas que **falharam**,
onde uma release falha se for seguida, em até 7 dias, por uma release
corretiva. Releases publicadas nos últimos 7 dias da janela de observação não
são avaliadas (censura).

O CFR (a), proxy de CI, é `falhas ÷ (falhas + sucessos)` sobre os workflow runs
de push no default branch. Pelo campo `conclusion`, `failure`, `timed_out` e
`startup_failure` são falhas; `cancelled`, `skipped`, `neutral`,
`action_required`, `stale` e execuções em andamento são **ignorados** e não
entram no cálculo.

**Validação da heurística.** [PENDENTE. Precisão, recall e F1 da heurística
frente aos rótulos manuais da amostra-ouro, calculados por
`metricas.cfr.avaliar_heuristica`. Nenhum valor deve ser escrito aqui antes de
a rotulagem existir e o cálculo ser executado.]

| Métrica | Valor |
| --- | --- |
| Precisão | [a calcular] |
| Recall | [a calcular] |
| F1 | [a calcular] |
| N releases avaliadas | [a calcular] |

### Ameaça à validade associada

Como ameaça à validade de construto, a heurística pode classificar
erroneamente releases que incrementam o número de patch por razões que não
correspondem a correção de defeito — por exemplo, atualizações de
dependências, ajustes de documentação ou releases de infraestrutura
publicadas como patches por convenção da equipe. A busca por `fix` também
encontra mensagens que não descrevem correções. Da mesma forma, releases
corretivas que incrementam versões minor ou major (por acompanharem uma
funcionalidade nova junto à correção) não são capturadas pelo critério
SemVer, podendo gerar falsos negativos.
