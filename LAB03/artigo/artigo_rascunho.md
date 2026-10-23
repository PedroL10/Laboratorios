# Velocidade e estabilidade em projetos open-source: uma mineração das métricas DORA em repositórios do GitHub

> **Rascunho de trabalho (#67).** Texto para ser transposto para o template SBC
> (`artigo.docx` / Overleaf). Trechos entre `[colchetes]` dependem dos resultados da
> coleta e são preenchidos a partir dos arquivos indicados em `resultados/`.
> Nenhum número entre colchetes deve ir para a versão final sem ter sido gerado
> pelos scripts de `analise/`.

---

## 1. Introdução

*(Mantida da versão da Sprint 1, em `artigo.docx`: contexto das métricas DORA,
o problema dos proxies, as sete RQs e as hipóteses H1 a H7, escritas antes da
análise dos dados.)*

---

## 2. Metodologia

### 2.1. Fonte de dados e ferramenta de coleta

Os dados foram coletados das APIs públicas do GitHub por um pipeline próprio,
escrito em Python, que usa apenas a biblioteca `requests` — sem bibliotecas
prontas de acesso à API, como exige o enunciado. Quase todas as consultas usam
a API REST; a API GraphQL é usada só para listar as tags de cada repositório já
ordenadas pela data do commit apontado, o que a API REST não oferece.

O pipeline é executado com um único comando (`python -m pipeline --config
config.yaml`), lê o token de acesso de uma variável de ambiente e grava em disco
cada resposta da API. Se a execução for interrompida (cota esgotada, queda de
rede, interrupção manual), rodar o mesmo comando retoma a coleta de onde parou,
sem repetir chamadas. Quando a cota de requisições acaba, o pipeline lê os
cabeçalhos `X-RateLimit-Reset` e espera a renovação; erros 5xx e quedas de
conexão são repetidos com *backoff* exponencial (1, 2, 4, 8 e 16 s). As funções
de cálculo das métricas são cobertas por testes automatizados (pytest), com
cobertura de 100% do módulo de métricas, executados a cada *push* pelo GitHub
Actions do próprio repositório do grupo.

### 2.2. Janela de observação

A janela de observação tem 12 meses: de 01/10/2025 a 30/09/2026, inclusive nas
duas pontas (52,14 semanas). Só entram nos cálculos as releases publicadas e os
*workflow runs* criados dentro dela.

### 2.3. Seleção dos repositórios

A Tabela 1 mostra o funil de seleção, gerado automaticamente pelo pipeline
(`resultados/funil_selecao.md`).

1. **Candidatos.** A busca do GitHub (`stars:>1000`) devolve no máximo 1.000
   resultados por consulta. Para obter mais candidatos, a busca foi fatiada por
   faixas de estrelas, dos mais estrelados para os menos, até reunir 2.000
   candidatos.
2. **Uso de GitHub Actions.** Foram descartados os candidatos sem nenhum
   workflow (`total_count = 0` em `/actions/workflows`).
3. **Critério mínimo de inclusão.** Em ordem decrescente de estrelas, cada
   candidato foi avaliado até que 300 repositórios cumprissem, dentro da janela,
   ao menos 5 releases publicadas e 50 workflow runs válidos no *default branch*.

**Tabela 1 – Funil de seleção.**

| Etapa | Repositórios | Descartados | Motivo |
| --- | ---: | ---: | --- |
| Candidatos da busca | 2.000 | – | – |
| Usam GitHub Actions | 1.727 | 273 | sem workflows |
| Avaliados pelo critério | 646 | 1.081 | não avaliados (amostra já completa) |
| ≥ 5 releases na janela | 347 | 299 | menos de 5 releases |
| ≥ 50 runs válidos (amostra final) | **300** | 47 | menos de 50 runs válidos |

**Caracterização da amostra.** Os 300 repositórios têm mediana de 63.734
estrelas (Q1 = 49.199; Q3 = 91.597; mínimo de 41.024), 473 contribuidores
(Q1 = 222; Q3 = 1.066) e 2.254 dias de idade no fim da janela (Q1 = 888;
Q3 = 3.929). 49 deles foram criados dentro da própria janela. As linguagens
principais mais frequentes são TypeScript (80), Python (72), Rust (32), Go (32)
e JavaScript (27). Os repositórios publicaram mediana de 28 releases na janela
(Q1 = 13; Q3 = 64; máximo de 2.584).

### 2.4. Definições operacionais

Todas as definições seguem as regras comuns da disciplina.

- **Deploy:** release publicada no GitHub (`draft = false`,
  `prerelease = false`). Pré-releases e tags ficam de fora da definição
  principal e são usadas como variantes na RQ 07.
- **Branch:** apenas o *default branch* de cada repositório.
- **Execuções de CI:** workflow runs do default branch disparados por `push`.
  Pelo campo `conclusion`, `success` é sucesso; `failure`, `timed_out` e
  `startup_failure` são falha; os demais (`cancelled`, `skipped`, `neutral`,
  `action_required`, `stale` ou vazio) são ignorados.
- **Data de um commit:** `commit.author.date`.

**RQ 01 – Deployment frequency.** Releases publicadas na janela divididas pelo
número de semanas da janela (52,14).

**RQ 02 – Lead time for changes.** Para cada release R da janela, os commits
incluídos são obtidos comparando R com a release anterior
(`compare/{anterior}...{R}`), mesmo que a anterior esteja fora da janela. A
primeira release da história do repositório não tem lead time. Variante (a), por
release: `data de R − data do commit mais antigo de R`, com o valor do
repositório dado pela mediana entre as suas releases. Variante (b), por commit:
`data de R − data de cada commit`, com a mediana de todos os commits de todas as
releases. Releases cujo compare devolve 404 (tag apagada ou reescrita) são
ignoradas e contadas.

**RQ 03 – Change failure rate.** Variante (a), proxy de CI:
`falhas ÷ (falhas + sucessos)` sobre os workflow runs. Variante (b), proxy de
entrega: uma release falha se for seguida, em até 7 dias, por uma release
corretiva; releases publicadas nos últimos 7 dias da janela não podem ser
avaliadas e ficam fora do denominador (censura). Uma release é considerada
**corretiva** quando a versão muda apenas no número de *patch* do SemVer
(ex.: 2.3.0 → 2.3.1) **ou** quando a maioria (≥ 50%) dos commits entre ela e a
release anterior tem `fix`, `revert` ou `hotfix` (palavra inteira) no título.
Essa é a versão v2 da heurística, adotada após a validação (Seção 2.8).

**RQ 04 – Tempo de recuperação.** As execuções de cada workflow são ordenadas
pelo início. Um episódio de falha começa na primeira falha após um sucesso e
termina na próxima execução bem-sucedida do mesmo workflow; sua duração é
`updated_at do sucesso − run_started_at da primeira falha`. O valor do
repositório é a mediana dos episódios de todos os seus workflows. Episódios sem
recuperação até o fim da janela são **censurados**: não entram na mediana, mas
são contados e reportados. Workflows que já começam a janela falhando também
ficam de fora — o sucesso que abriria o episódio está antes da janela, e o
início real é desconhecido; essa regra é uma decisão do grupo, pois o enunciado
não trata o caso.

**Classificação DORA.** Cada métrica é classificada em Elite, High, Medium ou
Low pelos cortes fixos da disciplina, e a categoria geral é a mediana dos pontos
(Elite = 4 … Low = 1), arredondada para baixo. Quando uma métrica não tem valor
(ex.: nenhum episódio de falha encerrado), a mediana usa as disponíveis.

### 2.5. Decisões de coleta

- **Teto de 1.000 runs por consulta.** A janela foi dividida em meses; antes de
  baixar um mês, o pipeline consulta quantos runs ele tem e, se passar de 1.000,
  divide o período ao meio até caber. Isso foi necessário: 130 dos 300
  repositórios atingiram o teto de 2.500 do `total_count` na contagem do
  critério de inclusão. [Dias que, sozinhos, passaram de 1.000 runs:
  `resultados/rq01_04/censura.md`.]
- **Commits entre releases.** O compare devolve até 250 commits por página e é
  paginado até o fim. Como as três unidades de deploy da RQ 07 repetem muitos
  pares de comparação, o resultado de cada par é guardado uma única vez e
  reaproveitado.
- **Volume.** A coleta envolveu [N] chamadas à API, com 22.100 releases na
  definição principal e mais de 477 mil workflow runs de push.

### 2.6. Variantes para a análise de sensibilidade (RQ 07)

| Combinação | Unidade de deploy | Lead time | CFR |
| --- | --- | --- | --- |
| C1 (referência) | release | (a) | (a) |
| C2 | release + pré-release | (b) | (b) |
| C3 | tag (data do commit apontado) | (b) | (a) |

Para cada par de combinações, calcula-se a proporção de repositórios que mudam
de categoria geral e o kappa de Cohen ponderado (linear).

### 2.7. Análise estatística

Todas as métricas são descritas por mediana e IQR. A RQ 05 usa a correlação de
Spearman entre frequência de deploy e cada variante do CFR. A RQ 06 compara as
quatro métricas (frequência, lead time (a), CFR (a) e tempo de recuperação)
entre os grupos de quatro fatores — linguagem principal (linguagens com menos de
10 repositórios agrupadas em "Outras"), quartis de estrelas, quartis de
contribuidores e quartis de idade —, com Kruskal-Wallis (ou Mann-Whitney, para
dois grupos), correção de Holm sobre os 16 testes e tamanho de efeito (ε² e
Cliff's δ).

### 2.8. Validação da heurística de release corretiva (amostra-ouro)

O protocolo da disciplina prevê 60 repositórios rotulados por três avaliadores.
Por restrição de tempo adotamos uma versão
reduzida: 20 repositórios sorteados com semente fixa (42) — os 20 primeiros do
sorteio de 60 — e 5 releases de cada, totalizando 100 releases. Os rótulos foram
produzidos a partir das release notes, dos títulos dos commits e
da descrição de cada repositório, **sem acesso à saída da heurística**. Para cada
repositório rotulou-se o tipo do projeto e se as releases representam entregas
reais; para cada release, se ela é corretiva. Com um único anotador, a
concordância entre avaliadores (kappa de Fleiss) não pôde ser calculada.

Das 100 releases, 47 foram rotuladas como corretivas. A primeira versão da
heurística (v1: *patch* **ou** algum commit com palavra-chave) obteve precisão
0,49, recall 0,98 e F1 0,66: marcou 93 das 100 releases, porque quase toda
release tem ao menos um commit de correção. Refinada para exigir a maioria dos
commits (v2), obteve precisão 0,62 (IC 95%: 0,49–0,75), recall 0,68 (0,55–0,80) e
F1 0,65 (0,53–0,75), com erros mais equilibrados. Nenhuma variante testada
atingiu F1 ≥ 0,70 (`artigo/versoes_heuristica_cfr.md`). Quanto ao tipo, os 20
repositórios se dividem em 8 aplicações/serviços, 6 bibliotecas/frameworks, 5
ferramentas CLI e 1 "outro"; em todos, as releases foram consideradas entregas
reais ao usuário.

---

## 3. Resultados

### 3.1. RQ 01 – Frequência de deploy

[`resultados/rq01_04/descritiva.md`: mediana e IQR em releases/semana.
`resultados/rq01_04/classificacao_c1.md`: % em cada faixa.
Figura: `resultados/rq01_04/figuras/distribuicoes.png`, painel RQ 01.]

### 3.2. RQ 02 – Lead time

[Mediana e IQR das variantes (a) e (b); diferença entre elas; releases ignoradas
por compare 404. Figura: painel RQ 02.]

### 3.3. RQ 03 – Change failure rate

[Mediana e IQR do CFR (a) e (b); releases censuradas no CFR (b). Figura: painel RQ 03.]

### 3.4. RQ 04 – Tempo de recuperação

[Mediana e IQR em horas; proporção de episódios censurados e repositórios sem
episódio encerrado (`resultados/rq01_04/censura.md`). Figura: painel RQ 04.]

### 3.5. Classificação DORA de referência (C1)

[`resultados/rq01_04/classificacao_c1.md` e `figuras/classificacao_c1.png`.]

### 3.6. RQ 05 – Frequência de deploy × taxa de falha

[`resultados/rq05/spearman.md`: ρ, p e n para o CFR (a) e o CFR (b).
Figura: `resultados/rq05/figuras/dispersao.png`.]

### 3.7. RQ 06 – Características dos repositórios

[`resultados/rq06/testes.md`: testes significativos após Holm e o tamanho de
efeito; `resultados/rq06/medianas.md`: qual grupo vai melhor.
Figura: `resultados/rq06/figuras/efeitos.png`.]

### 3.8. RQ 07 – Sensibilidade à definição operacional

[`resultados/rq07/concordancia.md`: % que mudou e kappa ponderado por par.
Figuras: `resultados/rq07/figuras/distribuicao.png` e `transicoes.png`.]

### 3.9. RQ 08 (bônus) – Rework rate

[`resultados/rq08/rework.md`: mediana do rework rate, comparação com o CFR (b) e Spearman.]

---

## 4. Discussão

Para cada hipótese, confrontar o esperado com o observado e explicar a diferença.

- **H1 (RQ 01).** Esperávamos a maioria em Medium e poucos em Elite. [Observado: …]
- **H2 (RQ 02).** Esperávamos a variante (a) consistentemente maior que a (b).
  [Observado: …] A variante (a) usa o commit mais antigo da release; um único
  commit "esquecido" — por exemplo, um branch de longa duração integrado perto
  da release — a faz explodir, enquanto pouco afeta a mediana de todos os
  commits da variante (b).
- **H3 (RQ 03).** Esperávamos CFR (a) entre 10% e 25% e CFR (b) menor. [Observado: …]
  O CFR (a) mede falha de pipeline — testes quebrados, *flakiness*, falhas de
  infraestrutura —, não falha em produção; o CFR (b) se aproxima mais da falha
  percebida pelo usuário, mas depende da heurística de release corretiva.
- **H4 (RQ 04).** Esperávamos mediana entre 1 hora e 1 dia, com cauda longa e
  parte dos episódios censurada. [Observado: …]
- **H5 (RQ 05).** Esperávamos correlação fraca ou nula com o CFR (a), em linha
  com a afirmação do DORA de que velocidade e estabilidade não são um
  *trade-off*, e correlação positiva com o CFR (b), por efeito da própria
  definição. [Observado: …] Correlação não implica causalidade.
- **H6 (RQ 06).** Esperávamos que mais contribuidores e mais estrelas se
  associassem a maior frequência e menor tempo de recuperação. [Observado: …]
- **H7 (RQ 07).** Esperávamos que cerca de um terço dos repositórios mudasse de
  categoria, com kappa entre 0,4 e 0,6. [Observado: …] As conclusões das RQ 01
  a 06 são robustas, ou dependem de uma escolha arbitrária de definição?

---

## 5. Ameaças à validade

**Validade de construto.**
- *Release não é deploy.* Bibliotecas publicam versões que só chegam à
  produção quando os usuários as adotam; a frequência de deploy mede, na
  verdade, a frequência de publicação.
- *Falha de CI não é falha em produção.* O CFR (a) conta testes quebrados e
  falhas de infraestrutura, que nunca chegaram a usuários.
- *Heurística de release corretiva.* Atualizações de dependências, de
  documentação ou de infraestrutura também saem como *patch*, e correções
  lançadas em versões *minor* ou *major* escapam ao critério. Na validação, a
  heurística final teve F1 = 0,65 (abaixo da meta de 0,70): o CFR (b) e o rework
  rate são aproximações com erro de cerca de um terço das classificações. Os
  rótulos de referência vêm de um único anotador automatizado (IA), em amostra
  reduzida (100 releases), e as variantes foram comparadas na mesma amostra.
- *Data do commit.* `commit.author.date` registra quando a mudança foi escrita;
  *rebases* e *squash merges* podem deslocá-la, encurtando ou alongando o lead time.
- *Tags.* Na variante C3, todas as tags do repositório são consideradas; em
  monorepos com tags por pacote (`pacote@1.2.3`), tags de pacotes diferentes
  são comparadas entre si.

**Validade interna.**
- 49 dos 300 repositórios foram criados dentro da janela; a frequência
  calculada sobre 52,14 semanas os subestima.
- Workflows auxiliares (documentação, *lint*, tarefas de dependências) entram
  no CFR (a) e no tempo de recuperação com o mesmo peso dos testes principais.
- Censura: episódios de falha não recuperados até o fim da janela e releases dos
  últimos 7 dias ficam fora das medianas. [Proporções em `censura.md`.]
- [Dias com mais de 1.000 runs têm runs incompletos: N repositórios.]

**Validade externa.**
- A amostra é formada pelos repositórios mais estrelados do GitHub (todos com
  mais de 41 mil estrelas). Projetos populares e abertos não representam
  projetos corporativos, que é o contexto das pesquisas do DORA.
- O critério de inclusão (≥ 5 releases e ≥ 50 runs) seleciona projetos ativos e
  que publicam releases; projetos que entregam por tags ou de forma contínua,
  sem release, ficam de fora.

**Validade de conclusão.**
- Na RQ 06 foram feitos 16 testes; a correção de Holm controla os falsos
  positivos, mas reduz o poder estatístico.
- Grupos pequenos (algumas linguagens) foram agrupados em "Outras", o que mistura
  ecossistemas diferentes.
- A RQ 05 é correlacional: não permite concluir causalidade.

---

## 6. Replicação cruzada

[Entrega final: relato da execução do pipeline de outro grupo e das Issues recebidas.]

---

## Repositório

Código, dados e GitHub Projects: https://github.com/PedroL10/Laboratorios

## Referências

- DORA. *Accelerate State of DevOps Reports* e *DORA's software delivery metrics: the four keys*. https://dora.dev
- Forsgren, N.; Humble, J.; Kim, G. (2018). *Accelerate: The Science of Lean Software and DevOps*. IT Revolution.
- Landis, J. R.; Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*.
- Romano, J. et al. (2006). Appropriate statistics for ordinal level data.
- Wohlin, C. et al. (2012). *Experimentation in Software Engineering*. Springer.
