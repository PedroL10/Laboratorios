# Dados reais

Amostra de 60 PRs usada para calibrar a simulação e para a aplicação final dos testes.
Os dados estão em [prs.csv](prs.csv).

| Campo | Valor |
| --- | --- |
| Repositório de origem | [TheHPXProject/hpx](https://github.com/TheHPXProject/hpx) |
| Bot de revisão | CodeRabbit (`coderabbitai[bot]`) |
| Data da coleta | 2026-11-05 |
| Como foi coletado | API de busca do GitHub, com `python -m lab04.coleta` (cerca de 1 minuto) |
| Observações por grupo | 30 (sorteadas com a semente 42) |

## Por que este repositório

O CodeRabbit passou a atuar de forma contínua no `hpx` em julho de 2026. Entre os PRs
mergeados e abertos de julho a setembro, todos os de autores humanos têm review ou
comentário do bot. Antes disso, quase nenhum tem. Por isso, o estudo compara um período
antes e um período depois da adoção.

## Critérios dos grupos

| Critério | `sem_bot` | `com_bot` |
| --- | --- | --- |
| PR aberto em | 2026-03-01 a 2026-05-31 | 2026-07-01 a 2026-09-30 |
| Atuação do CodeRabbit | Nenhuma | Review ou comentário |
| PRs elegíveis | 209 | 159 |

Critérios comuns aos dois grupos:

- **Somente PRs mergeados.** PRs fechados sem merge não têm tempo até o merge.
- **Somente autores humanos.** PRs abertos por bots, como o Dependabot, ficam de fora.
- **Sem review do Copilot.** Ele atua nos dois períodos e confundiria a comparação.
- **Merge em até 30 dias (720 h).** Os PRs de setembro tiveram só 36 dias para serem
  mergeados até a coleta. Sem esse limite, o grupo antigo teria mais tempo para acumular
  PRs longos. O limite também garante que os PRs de `sem_bot` foram mergeados antes da
  adoção do bot.

Junho de 2026 fica de fora por ser o período de transição: PRs abertos nesse mês
receberam review do bot quando já estavam em andamento.

## Validação

Reviews e comentários de 24 PRs da amostra (14 de `sem_bot` e 10 de `com_bot`) foram
consultados direto na API, sem usar a busca. Todos estavam no grupo correto, e nenhum tinha
atuação do Copilot. Uma segunda execução da coleta gerou um arquivo idêntico.

## Limitações

- **Não é um experimento.** Os períodos diferem em mais do que o bot, por exemplo nos
  autores ativos e no tipo de PR. A amostra não mede o tamanho dos PRs. Uma diferença entre
  os grupos não prova que o bot foi a causa.
- **Observações não totalmente independentes.** Há PRs do mesmo autor na amostra: `com_bot`
  tem 9 autores e `sem_bot` tem 18, e só 5 aparecem nos dois grupos.
- **Cauda cortada.** O limite de 30 dias remove os PRs mais demorados, então a assimetria
  real é maior que a da amostra.
- **Um único repositório.** Os resultados não valem automaticamente para outros projetos.

## Formato de `prs.csv`

| Coluna | Descrição |
| --- | --- |
| `pr` | Número do PR |
| `grupo` | `com_bot` ou `sem_bot` |
| `autor` | Login de quem abriu o PR |
| `atuacao_bot` | `review`, `comentario` ou `nenhuma` |
| `criado_em` | Data e hora de abertura (UTC) |
| `merge_em` | Data e hora do merge (UTC) |
| `horas_ate_merge` | Tempo entre a abertura e o merge, em horas |
