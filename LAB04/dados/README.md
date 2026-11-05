# Dados reais

Amostra usada para calibrar a simulação e para a aplicação final dos testes.

| Campo | Valor |
| --- | --- |
| Repositório de origem | _a preencher_ |
| Bot de revisão | _a preencher_ |
| Período dos PRs | _a preencher_ |
| Data da coleta | _a preencher_ |
| Como foi coletado | _a preencher_ |
| Critério para "com bot" e "sem bot" | _a preencher_ |
| Observações por grupo | _a preencher (meta: cerca de 30)_ |

## Formato de `prs.csv`

| Coluna | Descrição |
| --- | --- |
| `pr` | Número do PR |
| `grupo` | `com_bot` ou `sem_bot` |
| `criado_em` | Data e hora de abertura (UTC) |
| `merge_em` | Data e hora do merge (UTC) |
| `horas_ate_merge` | Tempo entre a abertura e o merge, em horas |
