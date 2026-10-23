### Change failure rate — variante (b), proxy de entrega

Definimos uma release R como **corretiva** quando, em relação à release anterior:

- a versão muda apenas no número de *patch* do Versionamento Semântico
  (ex.: `1.4.3` → `1.4.4`); **ou**
- a maioria (≥ 50%) dos commits entre as duas releases tem `fix`, `revert` ou
  `hotfix` (como palavra inteira) no título.

O CFR (b) do repositório é a proporção de releases avaliadas que **falharam**,
onde uma release falha se for seguida, em até 7 dias, por uma release
corretiva. Releases publicadas nos últimos 7 dias da janela de observação não
são avaliadas (censura).

O CFR (a), proxy de CI, é `falhas ÷ (falhas + sucessos)` sobre os workflow runs
de push no default branch. Pelo campo `conclusion`, `failure`, `timed_out` e
`startup_failure` são falhas; `cancelled`, `skipped`, `neutral`,
`action_required`, `stale` e execuções em andamento são **ignorados** e não
entram no cálculo.

**Validação da heurística.** A heurística foi comparada com rótulos de referência
em 100 releases (5 de cada um de 20 repositórios sorteados com semente 42). Os
rótulos foram produzidos por IA (Claude), com autorização do professor, a partir
das release notes, dos títulos dos commits e da descrição de cada repositório,
sem acesso à saída da heurística; 47 releases foram rotuladas como corretivas.

| Métrica | v1 | v2 (final) |
| --- | --- | --- |
| Precisão | 0,49 | 0,62 (IC 95%: 0,49–0,75) |
| Recall | 0,98 | 0,68 (IC 95%: 0,55–0,80) |
| F1 | 0,66 | 0,65 (IC 95%: 0,53–0,75) |
| Releases marcadas como corretivas | 93 | 52 |

A primeira versão (v1) considerava corretiva qualquer release com *algum* commit
de correção; como quase toda release tem um, ela marcou 93 das 100 releases e
superestimava o CFR (b). A v2 exige que a maioria dos commits seja de correção
quando a versão não é *patch*. Nenhuma variante atingiu F1 ≥ 0,70 (detalhes em
`versoes_heuristica_cfr.md`); os valores de CFR (b) e de rework rate devem ser
lidos como aproximações com erro da ordem de um terço das classificações.

### Ameaça à validade associada

Como ameaça à validade de construto, a heurística classifica como corretivas
releases *patch* que só atualizam dependências, documentação ou infraestrutura,
e não reconhece correções lançadas em versões *minor* ou *major* com poucos
commits de correção. Os rótulos de referência vêm de um único anotador
automatizado (IA), sem medida de concordância entre avaliadores (kappa de
Fleiss), e as variantes foram comparadas na mesma amostra usada para avaliá-las.
