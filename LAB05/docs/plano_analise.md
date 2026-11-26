# Plano de análise (C: Análise e Impacto)

Definido em 26/11/2026, antes da coleta completa. Segue as questões, métricas e hipóteses de
[gqm_hipoteses_ameacas.md](gqm_hipoteses_ameacas.md). Os números deste documento vêm de
[scripts/analisar_piloto.py](../scripts/analisar_piloto.py), com semente fixa 42.

## 1. Análise exploratória do piloto

São 10 requisições, todas com status 200, feitas em 19/11/2026 às 13h. O resultado está em
[resultados/piloto_descritiva.csv](../resultados/piloto_descritiva.csv).

| Estatística | Valor |
| --- | --- |
| Mínimo, mediana e máximo | 112 ms, 210 ms e 831 ms |
| Média | 304 ms |
| p95 | 710 ms |
| Coeficiente de variação | 0,80 |
| Assimetria | 1,13 (cauda à direita) |
| Lognormal ajustada | mediana 234 ms, σ = 0,70 |

**O que o piloto mostra para o plano:**

- **A latência é assimétrica à direita:** a média (304 ms) fica bem acima da mediana (210 ms).
  Isso confirma a escolha da mediana e do p95 no GQM, em vez da média.
- **A variação dentro do mesmo minuto é grande,** de 112 a 831 ms. Uma requisição isolada diz
  pouco. Por isso, cada rodada é resumida pela mediana de suas 5 requisições.
- **O formato do CSV funciona:** o tempo, o status e o período saem prontos para a análise.

**Limites do piloto:** foi uma única rodada, só no horário comercial, e com o formato antigo do
CSV. Ele não permite estimar quanto uma rodada varia em relação à outra, nem comparar os
períodos. Por isso, a simulação testa dois cenários de variação entre rodadas, e o plano será
recalibrado com a primeira semana da coleta completa.

## 2. Poder estimado por simulação (reaproveitando o LAB04)

**Desenho da simulação:**

- Rodadas de 5 requisições sorteadas da lognormal do piloto.
- 90 rodadas no horário comercial e 150 fora dele, o que se espera de 10 dias úteis.
- O efeito é o horário comercial ficar X vezes mais lento.
- 5.000 repetições por cenário.
- Resultado completo em [resultados/poder_simulado.csv](../resultados/poder_simulado.csv).

**Variação entre rodadas:**

- **Sem variação** (σ = 0): as rodadas só diferem pelo sorteio das requisições.
- **Moderada** (σ = 0,3): cada rodada tem um "estado da rede" próprio. É o cenário mais
  realista.

**Taxa de rejeição de H0 (%), com α = 0,05.** O fator 1,0 é o erro tipo I; os outros fatores
são o poder.

| Fator (comercial ÷ fora) | Variação entre rodadas | Mann-Whitney | Welch | Welch no log |
| --- | --- | --- | --- | --- |
| 1,0 (sem efeito) | nenhuma | 5,3 | 5,1 | 4,6 |
| 1,1 (+10%) | nenhuma | 46,5 | 43,3 | 47,3 |
| 1,2 (+20%) | nenhuma | 94,3 | 93,6 | 94,9 |
| 1,3 (+30%) | nenhuma | 99,9 | 99,9 | 99,9 |
| 1,0 (sem efeito) | moderada | 4,6 | 4,7 | 4,4 |
| 1,1 (+10%) | moderada | 29,9 | 26,8 | 31,4 |
| 1,2 (+20%) | moderada | 77,3 | 73,8 | 79,1 |
| 1,3 (+30%) | moderada | 97,7 | 96,5 | 98,1 |

**Leitura:**

- Os três testes mantêm o erro tipo I perto de 5%.
- **Duas semanas bastam para detectar uma diferença de 20% ou mais.** No cenário realista, o
  poder fica perto de 80%.
- Uma diferença de 10% tem boa chance de passar despercebida. Se o resultado não for
  significativo, a conclusão será "não detectamos diferença de 20% ou mais", e não "não há
  diferença".
- Os testes têm poder parecido. A escolha entre eles depende mais da robustez, porque a cauda
  real pode ser mais pesada que a do piloto.

## 3. Teste da hipótese principal

**Teste escolhido: Mann-Whitney bicaudal sobre as medianas das rodadas, com α = 0,05.**

- **Combina com H0.** A hipótese de [gqm_hipoteses_ameacas.md](gqm_hipoteses_ameacas.md) diz que
  "uma rodada de um período tem a mesma chance de ser mais lenta ou mais rápida que uma do
  outro". É exatamente o que o Mann-Whitney testa.
- **É robusto a picos.** Timeouts e rodadas muito lentas, que o piloto ainda não mostrou mas
  são comuns em APIs, distorcem a média e o t de Welch. O LAB04 mostrou isso: com cauda pesada,
  o Welch perdeu quase todo o poder.
- **Custa pouco poder.** Na simulação, ele fica a no máximo 2 pontos do melhor teste.

**Verificação de sensibilidade:** rodamos também o **t de Welch sobre o log** das medianas das
rodadas. Ele compara médias geométricas, que podem ser lidas como razões ("X% mais lento"). Se
os dois testes discordarem, relatamos os dois e discutimos o motivo, como no LAB04.

## 4. Tamanho do efeito

- **Razão das medianas (comercial ÷ fora),** com IC de 95% por bootstrap. É a medida principal,
  porque se lê direto: "o horário comercial foi 15% mais lento".
- **Diferença das medianas, em ms,** com IC de 95% por bootstrap. Ela alimenta o cálculo de
  impacto da Sprint 3.
- **Probabilidade de superioridade e r de rank-biserial,** que acompanham o Mann-Whitney. A
  interpretação usa os mesmos limites do LAB04: 0,1, 0,3 e 0,5.

O bootstrap é **por blocos de dia**, sorteando dias inteiros, e não rodadas soltas. Assim, ele
respeita a dependência entre rodadas do mesmo dia.

## 5. Hipóteses secundárias (exploratórias)

| Questão | Medida | Teste |
| --- | --- | --- |
| Q2: cauda | p95 da latência por requisição, em cada período | Diferença de p95 com IC por bootstrap em blocos de dia |
| Q3: disponibilidade | Taxa de sucesso (status 200) em cada período | Teste exato de Fisher |

Os p-valores das secundárias são corrigidos por Holm. Se houver menos de 5 falhas na coleta
toda, a Q3 é só descrita, sem teste.

## 6. Estatística descritiva e gráficos

- **Tabela por período:** número de rodadas e de requisições, taxa de sucesso, e mínimo, p25,
  mediana, média, p75, p95 e máximo da latência.
- **Perfil hora a hora:** boxplot da mediana das rodadas para cada hora de 0 a 23, com a faixa
  das 09h às 18h destacada. Mostra se o corte de "horário comercial" faz sentido e se as 13h, o
  horário da PTAX, se destacam.
- **Série no tempo:** mediana das rodadas por data e hora. Mostra mudanças de nível e dias com
  incidente.
- **Distribuição acumulada (ECDF)** dos dois períodos sobrepostos. Mostra a diferença na
  mediana e na cauda ao mesmo tempo.

As escalas seguem o GQM. Latência é de razão, então todas as estatísticas são permitidas. O
status HTTP é nominal, então usamos só contagens e proporções.

## 7. Limpeza e validação dos dados, antes da análise

1. Manter só as linhas com `origem = github-actions`.
2. Manter só os dias úteis: `dia_semana` de 0 a 4, sem feriados nacionais.
3. **Latência (M1, M3 e M4):** usar só as requisições com status 200.
4. **Taxa de sucesso (M5):** usar todas as requisições.
5. Descartar rodadas com menos de 3 requisições válidas, porque a mediana fica instável.
6. Contar as rodadas por hora e por dia, para identificar horas que o GitHub pulou.

O número de linhas removidas em cada passo será registrado, para que a limpeza seja rastreável.

## 8. Análises de sensibilidade

A conclusão principal é mais confiável se continuar a mesma nestes cenários:

| Cenário | Ameaça que verifica |
| --- | --- |
| Sem as rodadas das 12h às 14h | Divulgação da PTAX por volta das 13h (validade interna) |
| Um valor por dia e período, com Wilcoxon pareado por dia | Dependência entre rodadas do mesmo dia (validade de conclusão) |
| Sem os dias com incidente ou com muitas falhas | Eventos isolados (validade interna) |
| Corte de horário comercial em 08h–19h | Corte arbitrário de 09h–18h (validade de construto) |

## 9. Próximos passos

- **Depois da primeira semana de coleta:** recalibrar a simulação com as rodadas reais, que
  permitem estimar a variação entre rodadas, e confirmar se 2 semanas bastam.
- **Sprint 2:** implementar a limpeza (seção 7), a descritiva (seção 6), os testes (seções 3 e 5)
  e as sensibilidades (seção 8) sobre os dados da coleta completa.

## Como reproduzir

Dentro de `LAB05`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/analisar_piloto.py
```
