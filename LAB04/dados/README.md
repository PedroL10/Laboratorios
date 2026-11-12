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

## Forma da distribuição

Gerado por `python -m lab04`. As tabelas completas estão em
[forma_distribuicao.csv](../resultados/forma_distribuicao.csv) e
[ajustes_distribuicao.csv](../resultados/ajustes_distribuicao.csv).

| Medida | `sem_bot` | `com_bot` | Todos |
| --- | --- | --- | --- |
| Média (h) | 40,4 | 68,0 | 54,2 |
| Mediana (h) | 39,1 | 45,1 | 41,8 |
| Desvio padrão (h) | 34,0 | 65,5 | 53,6 |
| Coeficiente de variação | 0,84 | 0,96 | 0,99 |
| Assimetria | 0,93 | 1,86 | 2,15 |
| Outliers (Tukey) | 0 | 1 | 3 |
| Shapiro-Wilk, p em horas | 0,018 | 0,0002 | < 0,0001 |
| Shapiro-Wilk, p no log | 0,007 | 0,743 | 0,012 |

Diferença de AIC para o melhor ajuste de cada grupo (0 é o melhor; acima de 2 já indica
ajuste pior):

| Distribuição | `sem_bot` | `com_bot` | Todos |
| --- | --- | --- | --- |
| Gamma | 0,2 | 0,0 | 0,0 |
| Weibull | 0,0 | 0,3 | 0,0 |
| Lognormal | 6,4 | 0,1 | 7,2 |
| Normal | 14,1 | 22,7 | 48,1 |

O que os dados mostram:

- **Não são normais.** A assimetria é positiva nos dois grupos, e o Shapiro-Wilk rejeita a
  normalidade em ambos. A normal é o pior ajuste em todos os casos.
- **A lognormal não é a melhor opção.** O log de `sem_bot` continua assimétrico, agora para
  a esquerda, e o Shapiro-Wilk rejeita a normalidade do log.
- **Gamma e Weibull empatam.** As duas ajustam bem os grupos e a amostra inteira. As formas
  ficam perto de 1, ou seja, próximas de uma exponencial.
- **`com_bot` tem mais dispersão.** O desvio padrão é quase o dobro, mas a média também
  cresce e o coeficiente de variação fica parecido. Esse padrão combina com uma mudança de
  escala, em que os tempos são multiplicados por um fator.
- **Há poucos outliers.** O limite de 30 dias corta a cauda da amostra.

O teste de Kolmogorov-Smirnov não foi usado para escolher a distribuição, porque fica
permissivo demais quando os parâmetros são estimados da própria amostra.

### Da sugestão inicial à simulação final

Na análise inicial, sugerimos a Gamma de `sem_bot` (forma 1,04; escala 38,69 h) como base
e uma lognormal com desvio no log de cerca de 1,2 para a Q3. Esses valores eram sugestões
de planejamento e não são a configuração final executada por `python -m lab04`.

| Uso final | Distribuição e parâmetros | Base da escolha |
| --- | --- | --- |
| G1 e teste de exemplo, `sem_bot` | Weibull: forma 1,07; escala 41,35 h | Menor AIC do grupo `sem_bot` |
| G1 e teste de exemplo, `com_bot` | Gamma: forma 1,25; escala 54,52 h | Menor AIC do grupo `com_bot` |
| Q1 e Q2, referência e amostra pequena | Gamma: forma 1,07; escala 50,59 h | Menor AIC da amostra inteira, reunindo os 60 PRs |
| Q3, cauda pesada | Lognormal: σ do log = 2,5; mediana 41,8 h | Mediana da amostra inteira com dispersão ampliada para um teste de estresse |

O G1 reproduz cada grupo separadamente. Nas simulações de erro tipo I e poder, os dois
grupos partem da mesma distribuição ajustada à amostra inteira, para garantir H₀
verdadeira antes de introduzir o efeito. Usar ajustes distintos por grupo nessa etapa
confundiria diferenças do gerador com o efeito controlado.

As simulações usam 30 observações por grupo na referência e na cauda pesada, e 10 na
situação de amostra pequena. Os tempos de um grupo são multiplicados pelos fatores 1;
1,25; 1,5; 1,75; 2 e 2,5: fator 1 significa ausência de efeito. São 10.000 repetições por
combinação, semente 42 e α = 0,05. O fator multiplicativo foi motivado pelos coeficientes
de variação próximos dos grupos reais (0,84 e 0,96).

A lognormal final de Q3 não pretende ajustar o HPX: σ do log = 2,5 é deliberadamente mais
extremo que o valor próximo de 1,2 observado na amostra inteira. Os parâmetros positivos
têm localização fixada em zero. Os números da tabela são arredondados; o código reajusta
e usa os valores completos. Detalhes do cenário e da cronologia das expectativas estão
em [cenario.md](../cenario.md).

Com 30 observações por grupo, esses ajustes têm bastante incerteza. Eles servem para deixar
a simulação realista, e não para afirmar qual distribuição gerou os dados.

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
