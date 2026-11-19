# Evidências dos três critérios: API SGS do Banco Central

Este documento mostra que a API SGS atende aos três critérios da seção 2a do enunciado: o
software é real, está em operação e tem alto impacto. A tabela-resumo fica em
[decisao_software_caminho.md](decisao_software_caminho.md).

Todos os acessos foram feitos em **19/11/2026, por volta das 20h45 (horário de Brasília)**.
As consultas automáticas usaram uma requisição por endereço, com pelo menos 1 segundo de
intervalo.

## Real

O SGS (Sistema Gerenciador de Séries Temporais) é o sistema oficial do Banco Central do Brasil
para publicar séries econômicas: câmbio, juros, inflação, crédito, entre outras. A API REST
responde em `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`.

| Evidência | Fonte |
| --- | --- |
| A API é publicada e documentada pelo próprio BCB no Portal de Dados Abertos, que traz o endereço, os parâmetros e um recurso JSON para cada série. | [Portal de Dados Abertos do BCB: série 11, Selic](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic/resource/b73edc07-bbac-430c-a2cb-b1639e605fa8) |
| O Plano de Dados Abertos do BCB (2025–2027), documento oficial, aponta o SGS como o sistema de publicação de várias bases do inventário de dados do banco, como base monetária, crédito, IBC-Br e TJLP. | [Plano de Dados Abertos do BCB, maio/2025 a abril/2027, anexo 2](https://www.bcb.gov.br/content/acessoinformacao/acesso_informacao_docs/Plano_Dados_Abertos_BC.pdf) |

## Em operação

| Evidência | Fonte |
| --- | --- |
| Em 19/11/2026, às 20h47, a API respondeu com HTTP 200 e devolveu o dólar PTAX **do próprio dia**: `[{"data":"19/11/2026","valor":"5.8889"}]`. A série é atualizada a cada dia útil. | [Série 1, último valor](https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json) |
| A coleta piloto de 19/11/2026 teve 10 de 10 requisições com HTTP 200. | [dados/coleta_piloto.csv](../dados/coleta_piloto.csv) |
| A API recebe manutenção ativa: desde 26/03/2025, o BCB limita o volume de dados por consulta e exige filtros, com períodos de no máximo 10 anos. | [Portal de Dados Abertos do BCB: série 11, Selic](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic/resource/b73edc07-bbac-430c-a2cb-b1639e605fa8) |
| O Portal de Dados Abertos lista **4.261 conjuntos de dados**, dos quais **4.241 têm recurso em JSON**, o formato da API SGS. | [API do portal (CKAN), `package_search`](https://dadosabertos.bcb.gov.br/api/3/action/package_search?rows=0) |

## Alto impacto

O BCB não publica quantas requisições a API recebe. Por isso, medimos o impacto de duas formas
indiretas: o uso das bibliotecas que existem só para consumir os dados do BCB e a importância
dos dados que a API entrega.

### Uso das bibliotecas que consomem a API

| Biblioteca | Linguagem | Downloads | Fonte |
| --- | --- | --- | --- |
| `python-bcb` | Python | **78.019 no último mês** (19.606 na última semana) | [pypistats.org](https://pypistats.org/packages/python-bcb) |
| `sgs` | Python | 4.213 no último mês | [pypistats.org](https://pypistats.org/packages/sgs) |
| `rbcb` | R | 13.169 em 12 meses (nov/2025 a out/2026) | [cranlogs](https://cranlogs.r-pkg.org/downloads/total/2025-11-01:2026-10-31/rbcb) |
| `GetBCBData` | R | 10.360 em 12 meses (nov/2025 a out/2026) | [cranlogs](https://cranlogs.r-pkg.org/downloads/total/2025-11-01:2026-10-31/GetBCBData) |

Somando só as bibliotecas Python, são cerca de **82 mil downloads por mês**, ou quase **1
milhão por ano**. Cada download é alguém, ou algum sistema, preparando-se para consumir dados do
BCB por código.

### Importância dos dados entregues

| Evidência | Fonte |
| --- | --- |
| A PTAX, série 1 da API, é a referência usada pela B3 para liquidar contratos futuros de moedas. | [Ofício Circular B3 022/2025](https://www.b3.com.br/data/files/AB/B6/22/F5/67F77910AE23A679AC094EA8/OC%20022-2025-VPC%20ALTERACAO%20NOS%20CONTRATOS%20FUTUROS%20DE%20MOEDAS%20ESTRANGEIRAS%20PARES%20EM%20BRL_PORT.pdf) |
| A B3 mantém uma metodologia de contingência para o dia em que o BCB não divulgar a PTAX, o que mostra que o mercado depende dessa publicação. | [B3: metodologia da taxa de contingência da PTAX](https://www.b3.com.br/data/files/5C/23/F5/BB/8C021810C493CD08AC094EA8/Metodologia%20de%20calculo%20da%20taxa%20de%20Contingencia%20em%20caso%20de%20indispobilidade%20da%20Ptax.pdf) |
| A metodologia oficial da PTAX é definida em norma do BCB. | [Resolução BCB nº 45/2020](https://www.normasbrasil.com.br/norma/resolucao-45-2020_404869.html) |

## O que essas evidências não mostram

Estes limites também valem para a ameaça de validade externa e para a seção de impacto.

- **Downloads não são usuários.** Um mesmo projeto baixa a biblioteca várias vezes, por exemplo
  a cada execução de CI. Os números mostram que o uso é amplo, mas não contam pessoas nem
  empresas.
- **`python-bcb` não usa só o SGS.** A biblioteca também acessa outras APIs do BCB, como a de
  expectativas de mercado (Focus) e a de PTAX em OData. Os downloads medem o interesse pelos
  dados do BCB como um todo, não só pelo endpoint que vamos medir.
- **A B3 depende da PTAX, não necessariamente da API SGS.** A mesma taxa também é publicada por
  outros canais do BCB. A evidência mostra a importância do dado, e não o tráfego da API.
- **Não há número oficial de requisições.** O Plano de Dados Abertos diz que o BCB acompanha os
  acessos, mas o número não é publicado. Se o grupo quiser um número oficial, pode pedir pela Lei
  de Acesso à Informação, no Fala.BR. O prazo de resposta é de 20 dias, prorrogáveis por mais 10.

## Observação sobre ética

Em 19/11/2026, `https://api.bcb.gov.br/robots.txt` respondeu **HTTP 404**: o domínio não tem
`robots.txt`, então não há restrição declarada para robôs. Mesmo assim, a coleta mantém o limite
de 1 requisição por segundo exigido pelo enunciado.
