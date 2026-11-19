# LAB05 — Divisão de tarefas da Sprint 1 (Lab05S01)

Enunciado completo: [enunciado_lab05.md](enunciado_lab05.md). Este laboratório é o mais
aberto do semestre: o trio escolhe o software, a pergunta de pesquisa, o caminho do
estudo, as métricas e o formato final. A Sprint 1 (5 pontos) entrega:

- software real, em operação e de alto impacto, com evidências dos três critérios
  (seção 2a do enunciado);
- pergunta de pesquisa + caminho(s) escolhido(s) (seção 2b);
- primeira versão das 7 categorias de pesquisa (seção 3, Aula 8), com justificativa;
- plano de coleta e de análise;
- coleta piloto.

Mantendo a continuidade dos papéis já usados nos laboratórios anteriores (ver
[DIVISAO_SPRINT2.md](../LAB03/DIVISAO_SPRINT2.md) do LAB03) e a divisão sugerida pelo
próprio enunciado (seção 6):

- **A — PedroL10**: Planejamento e Método.
- **B — EnricoBessa**: Instrumentação e Operação.
- **C — bitpickle (Péricles Pires)**: Análise e Impacto.

Critério de divisão: tarefas em volume e dificuldade comparáveis entre os três, cada uma
rastreável por pelo menos uma Issue com código ou documento commitado (regra da seção 10
do enunciado geral da disciplina — sem isso, a nota individual da sprint é zerada).

## Tarefa comum aos três (decisão em grupo, antes de dividir o resto) — CONCLUÍDA

Decisão registrada em 2026-11-19, revisada no mesmo dia (Docker não estava disponível na
máquina de coleta), detalhada em
[docs/decisao_software_caminho.md](docs/decisao_software_caminho.md):

- **Software:** API SGS do Banco Central do Brasil (dados abertos — evidências a
  confirmar por A).
- **Caminho (seção 2b):** medir o serviço de fora, coletando latência de requisições HTTP
  à API, respeitando no máximo 1 requisição/segundo.
- **Pergunta de pesquisa:** o tempo de resposta da API varia entre horário comercial
  (09h–18h) e fora dele, em dias úteis?

Falta ainda: abrir/confirmar o quadro no GitHub Projects e linkar no README, e combinar o
formato final do documento/apresentação (seção 8) — não precisa estar pronto nesta sprint.

## A — PedroL10 — Planejamento e Método

1. Levantar e documentar as evidências dos três critérios (real / em operação / alto
   impacto) do software escolhido, com números e fontes (seção 2a).
2. Redigir a pergunta de pesquisa e justificar o(s) caminho(s) escolhido(s) (seção 2b).
3. Classificar o estudo nas **7 categorias de pesquisa** da Aula 8 (natureza, objetivos,
   abordagem, procedimentos, tempo, controle, nível de evidência), com justificativa para
   cada uma (primeira versão — será revisada na Sprint 3).
4. Formular hipóteses (se o caminho envolver teste de hipótese) ou objetivo no template
   GQM de Basili (pergunta + métricas), e levantar as principais ameaças à validade
   esperadas (conclusão, interna, construto, externa) para já desenhar mitigação.
5. Documento: seção de método (software, critérios, pergunta, categorias, GQM/hipóteses).

## B — EnricoBessa (você) — Instrumentação e Operação — FEITO NESTA SPRINT

1. ~~Montar o ambiente ou roteiro de coleta~~ — feito: script Python puro (sem
   dependências externas), sem precisar de Docker nem de instalação com admin.
2. ~~Implementar os scripts de coleta~~ — feito:
   [scripts/coletar_latencia_bcb.py](scripts/coletar_latencia_bcb.py), que mede a
   latência de requisições à API do BCB e salva em CSV.
3. ~~Levantar e documentar os cuidados de ética aplicáveis~~ — feito: `robots.txt` de
   `api.bcb.gov.br` checado (sem restrição), limite de 1 req/s aplicado no próprio
   script, nenhum dado pessoal coletado. Ver seção "Cuidados de ética aplicados" em
   [docs/decisao_software_caminho.md](docs/decisao_software_caminho.md).
4. ~~Executar a coleta piloto~~ — feito: 10 requisições em
   [dados/coleta_piloto.csv](dados/coleta_piloto.csv), 10/10 com status 200.
5. Documento: feito em [docs/plano_coleta.md](docs/plano_coleta.md) (ambiente, script,
   piloto, proposta de plano para a coleta completa da Sprint 2).

**Pendente ainda para fechar a entrega de B:** abrir a Issue no GitHub e commitar este
trabalho referenciando o número dela (regra da seção 10 — sem isso a tarefa não conta
pra nota individual).

## C — bitpickle (Péricles Pires) — Análise e Impacto

1. Definir o **plano de análise**: estatística descritiva prevista, teste de hipótese
   adequado à escala de cada métrica (se houver), e como será calculado o tamanho do efeito.
2. Levantar as fontes públicas de números de impacto do software escolhido (clientes do
   fornecedor, downloads em PyPI/npm/Docker Hub, DB-Engines, Stack Overflow Developer
   Survey, painéis gov.br etc.), com link e data de acesso, para já ter a base da seção de
   impacto (seção 5).
3. Rodar uma análise exploratória rápida sobre os dados da coleta piloto de B, só para
   confirmar que o plano de análise da sprint 1 é aplicável ao formato de dado que está
   saindo (sem necessidade de resultado definitivo ainda).
4. Esboçar, com números públicos, um primeiro rascunho de frase de impacto (modelo da
   seção 5 do enunciado: "a diferença medida equivale a X horas/recursos por período,
   considerando Y usuários/transações").
5. Documento: seção de plano de análise + rascunho inicial de impacto (com fontes).

## Observações

- Nenhuma tarefa de código ou documento conta sem commit referenciando o número da Issue
  (`git commit -m "#NUMERO ..."`), seguindo a regra já usada nos laboratórios anteriores.
- A tarefa de C (análise exploratória da coleta piloto) depende da coleta piloto de B;
  combinar prazos entre os três para não travar a sprint.
- A escolha do software e do caminho (tarefa comum) precisa estar fechada antes de A, B e
  C conseguirem avançar nas tarefas individuais — resolver isso primeiro, com o professor
  na S01 se precisar de validação.
