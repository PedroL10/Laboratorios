# Plano de coleta e coleta piloto (B: Instrumentação e Operação)

## Instrumento

Script: [scripts/coletar_latencia_bcb.py](../scripts/coletar_latencia_bcb.py).

- **O que faz:** envia requisições HTTP GET à série 1 (dólar PTAX) da API SGS do Banco Central
  (`api.bcb.gov.br`) e mede o tempo entre o envio e o recebimento da resposta, ou seja, a
  latência ponta a ponta.
- **Intervalo:** respeita no mínimo 1 segundo entre requisições, definido na constante
  `INTERVALO_MINIMO_SEGUNDOS`.
- **Dados:** não usa autenticação e não envia nem recebe dados pessoais.
- **Rodada:** cada execução do script é uma **rodada** de N requisições seguidas.

| Coluna | Conteúdo |
| --- | --- |
| `rodada` | Início da rodada; identifica as requisições que foram feitas juntas |
| `timestamp` | Momento da requisição, sempre no fuso de Brasília (com `-03:00`) |
| `data`, `dia_semana`, `hora` | Data, dia da semana (0 = segunda ... 6 = domingo) e hora, em Brasília |
| `periodo` | `comercial` se 09h–18h, senão `fora_comercial` |
| `latencia_ms` | Latência ponta a ponta, em milissegundos |
| `status_http`, `bytes`, `erro` | Resultado da requisição; `erro` fica vazio quando dá certo |
| `origem` | Onde a coleta rodou: `github-actions` ou `local` |

### Ajustes feitos depois do piloto (26/11/2026)

- **Fuso fixo de Brasília.** Antes, o script usava o relógio da máquina. No GitHub Actions, que
  roda em UTC, as 14h viravam 17h e caíam no período errado.
- **Novas colunas:** `rodada`, `data`, `dia_semana`, `bytes` e `origem`.
  - `dia_semana` separa os dias úteis, que fazem parte da pergunta.
  - `rodada` define a unidade de análise.
  - `bytes` confirma que a resposta veio completa.
- **User-Agent próprio**, que identifica a coleta como acadêmica, sem dados pessoais.
- **Falhas de rede registradas sem interromper a coleta**, como timeout ou conexão recusada.

## Coleta piloto (rodada em 19/11/2026)

Foram 10 requisições em sequência, no horário comercial (13h). O resultado está em
[dados/coleta_piloto.csv](../dados/coleta_piloto.csv), no formato antigo, sem as novas colunas.

- As 10 requisições tiveram status HTTP 200, sem nenhuma falha.
- A latência ficou entre cerca de 112 ms e 831 ms, com bastante variação mesmo dentro do mesmo
  minuto.

## Plano da coleta completa (Sprint 2)

| Item | Decisão | Por quê |
| --- | --- | --- |
| Onde roda | GitHub Actions, workflow [lab05-coleta.yml](../../.github/workflows/lab05-coleta.yml) | A rede e a máquina são sempre as mesmas, e ninguém precisa deixar o computador ligado de madrugada. A internet de casa fica mais lenta à noite e se confundiria com o período "fora do comercial". |
| Frequência | 1 rodada por hora, no minuto 17, 24 horas por dia | Cobre os dois períodos todos os dias, sem depender de alguém lembrar de rodar. |
| Tamanho da rodada | 5 requisições, 1 por segundo | São 120 requisições por dia, muito abaixo do limite ético do enunciado. |
| Duração | No mínimo 2 semanas, a partir do push do workflow | Com 10 dias úteis: cerca de 90 rodadas no horário comercial e 150 fora dele. |
| Onde ficam os dados | `LAB05/dados/coleta.csv`, no branch `lab05-dados` | Os commits automáticos de cada hora ficam fora do master, e ninguém precisa dar pull antes de cada push. |
| Unidade de análise | A rodada (por exemplo, a mediana das 5 requisições) | Requisições do mesmo minuto medem o mesmo estado da rede e não são independentes. Tratá-las como amostras separadas inflaria o poder do teste. |
| Dias analisados | Segunda a sexta, sem feriados nacionais | É o que a pergunta de pesquisa define. Fins de semana e feriados ficam no CSV e podem entrar em uma análise extra. |

### Como acompanhar e encerrar

- **Ver as rodadas:** aba **Actions** do repositório, workflow `lab05-coleta`.
- **Ver os dados:** branch `lab05-dados`, arquivo `LAB05/dados/coleta.csv`.
- **Pausar ou encerrar:** Actions > `lab05-coleta` > **Disable workflow**.
- **Levar os dados para o master no fim da coleta:**

  ```bash
  git fetch origin lab05-dados
  git checkout origin/lab05-dados -- LAB05/dados/coleta.csv
  ```

### Limites conhecidos

- **Atraso do agendamento:** o GitHub pode atrasar ou pular execuções agendadas em horários de
  pico. Isso não distorce os dados, porque o horário real fica registrado em cada linha, mas
  algumas horas podem ter menos rodadas.
- **Rede da coleta:** a máquina do GitHub fica fora do Brasil. A latência inclui esse trecho de
  rede, que é o mesmo em todas as rodadas. O resultado vale para quem consome a API a partir
  dessa rede (validade externa).
- **Conexão nova a cada requisição:** cada requisição abre uma conexão, então a latência inclui
  DNS, TCP e TLS. Isso imita um cliente simples, mas não separa o tempo de rede do tempo do
  servidor (validade de construto).

## Ética

- **Robôs:** em 19/11/2026, `api.bcb.gov.br/robots.txt` respondeu HTTP 404, ou seja, não há
  restrição declarada. Antes de ativar a coleta completa, confira de novo.
- **Volume:** no máximo 1 requisição por segundo, e só 5 por hora.
- **Dados pessoais:** a série consultada é um indicador público e agregado.

## Comandos

```bash
# Uma rodada local, de dentro de LAB05/scripts
python coletar_latencia_bcb.py --n 5 --saida ../dados/coleta_local.csv --origem local
```

Parâmetros:

- `--n`: requisições por rodada, padrão 5.
- `--saida`: CSV de saída. O script acrescenta linhas se o arquivo já existir.
- `--origem`: de onde a coleta foi feita.
