# Classificação do estudo nas 7 categorias de pesquisa (primeira versão)

Primeira versão, da Sprint 1. Ela será revisada na Sprint 3, depois da coleta completa
(seção 7 do enunciado). O estudo é o descrito em
[decisao_software_caminho.md](decisao_software_caminho.md): medir de fora a latência da API SGS
do Banco Central e comparar o horário comercial (09h–18h) com o horário fora dele, em dias
úteis.

## Resumo

| Categoria | Classificação | Justificativa em uma frase |
| --- | --- | --- |
| Natureza | Aplicada | Responde a uma pergunta prática de quem consome a API, sem propor teoria nova. |
| Objetivos | Descritiva, com comparação entre grupos | Descreve a latência e compara dois períodos, sem explicar a causa da diferença. |
| Abordagem | Quantitativa | A métrica é numérica (milissegundos), analisada com estatística descritiva e teste de hipótese. |
| Procedimentos | Pesquisa de campo com medição instrumentada | Mede o software real em produção, de fora, com um script de coleta automatizada. |
| Tempo | Longitudinal (curta duração) | Mede o mesmo serviço repetidamente ao longo de vários dias e horários. |
| Controle | Observacional (não experimental) | O período do dia não pode ser manipulado nem sorteado; só observamos o serviço como ele está. |
| Nível de evidência | Baixo a moderado: associação, não causa | É um estudo observacional, com um único ponto de medição e um único endpoint. |

## Justificativas

### 1. Natureza: aplicada

A pesquisa busca um conhecimento de uso imediato: saber se quem integra a API do BCB precisa
considerar o horário do dia, por exemplo ao definir timeouts, agendar rotinas ou fazer cache. Ela
não procura uma teoria geral sobre o desempenho de APIs, o que caracterizaria uma pesquisa
básica.

### 2. Objetivos: descritiva, com comparação entre grupos

- **Não é exploratória.** A pergunta e as hipóteses foram definidas antes da coleta, e não
  surgiram dos dados.
- **É descritiva.** O estudo descreve uma característica do software em operação: a
  distribuição da latência, com mediana, p95 e taxa de erros. Depois, compara essa característica
  entre dois grupos, horário comercial e fora dele.
- **Não é explicativa.** Mesmo que a latência mude entre os períodos, o estudo não tem como
  dizer **por quê**. A causa pode ser carga no servidor, cache, a rede do provedor ou a rede do
  próprio grupo. Explicar a causa exigiria acesso à infraestrutura do BCB.

### 3. Abordagem: quantitativa

A variável dependente é a latência em milissegundos, uma escala de **razão**: tem zero absoluto,
e faz sentido dizer que 400 ms é o dobro de 200 ms. Por isso, valem a média, a mediana, os
percentis e os testes paramétricos ou não paramétricos. O status HTTP é uma variável
**nominal**, analisada por proporção, como a taxa de erros. Não há coleta de opiniões nem de
texto, então não há componente qualitativo.

### 4. Procedimentos: pesquisa de campo com medição instrumentada

- O objeto é o **software em produção**, e não uma cópia em laboratório. Por isso, a pesquisa
  é de campo.
- Os dados são gerados pelo próprio grupo, com o instrumento
  [scripts/coletar_latencia_bcb.py](../scripts/coletar_latencia_bcb.py). Não são dados
  publicados por terceiros, o que caracterizaria uma pesquisa documental.
- O enunciado chama esse caminho de "medir o serviço de fora" (seção 2b).

### 5. Tempo: longitudinal, de curta duração

O plano de coleta mede o mesmo serviço várias vezes, em horários e dias diferentes. A variável
de interesse, o horário, só existe ao longo do tempo. Um estudo transversal, com uma única
rajada de medições, não responderia à pergunta. É de curta duração porque cobre dias ou poucas
semanas, e não meses. Por isso, não captura efeitos sazonais, como o fim de mês ou dias de
divulgação de indicadores.

### 6. Controle: observacional (não experimental)

- **O que o grupo controla:** o instrumento, que é o mesmo script; o endpoint, que é o mesmo
  para todas as requisições; o intervalo entre requisições; e a rede e a máquina de coleta.
- **O que o grupo não controla:**
  - O **tratamento**: o período do dia é uma característica do momento da medição, que o grupo
    não pode atribuir nem sortear.
  - O **estado do servidor**: carga, cache e versões mudam sem aviso.
  - A **rede entre o grupo e o BCB**.
- Sem manipulação nem sorteio do tratamento, o estudo não é um experimento controlado.
  Também não é um quase-experimento no sentido usual, porque não existe uma intervenção
  aplicada a um grupo e não ao outro. É um **estudo observacional comparativo**.

### 7. Nível de evidência: baixo a moderado, de associação e não de causa

- **Pontos que fortalecem:**
  - medição direta, sem depender de opinião;
  - muitas observações ao longo de vários dias;
  - instrumento e procedimento padronizados e versionados, o que permite reproduzir o estudo.
- **Pontos que enfraquecem:**
  - O estudo é observacional, então mostra se a latência está **associada** ao período, mas não
    que o período **causa** a mudança.
  - Há um único ponto de medição: uma rede e um local.
  - Há um único endpoint, a série 1 com o último valor.
  - O período de coleta é curto.
- Na hierarquia usual de evidência, que vai de revisões sistemáticas e experimentos controlados
  até a opinião de especialistas, o estudo fica no nível dos **estudos observacionais com
  medição controlada**. Ele é mais forte que relatos ou opinião, mas mais fraco que um
  experimento.

## O que isso significa para as conclusões

- O resultado será formulado assim: "no período estudado, medida a partir da rede X, a
  latência da API foi Y% maior/menor no horário comercial". Não vamos dizer "o horário
  comercial deixa a API mais lenta".
- A maior ameaça interna era a **rede do próprio grupo**, que também varia com o horário e se
  confundiria com o efeito do servidor. A coleta no GitHub Actions resolve essa parte, mas a
  diferença ainda pode vir de qualquer ponto do caminho até a API. Por isso, o estudo continua
  observacional. As ameaças estão em [gqm_hipoteses_ameacas.md](gqm_hipoteses_ameacas.md).

## O que pode mudar na revisão da Sprint 3

- **Tempo:** se a coleta durar menos que o planejado, a duração do estudo longitudinal precisa
  ser revista.
- **Procedimentos:** se o grupo combinar caminhos, a classificação passa a ser mista e o nível de
  evidência sobe. O enunciado valoriza essa combinação. Exemplos:
  - analisar dados de operação do BCB;
  - medir de dois pontos de rede diferentes para separar a rede do servidor.
- **Objetivos:** se a análise encontrar padrões não previstos, por exemplo um horário específico
  com picos, essa parte será declarada como exploratória.
