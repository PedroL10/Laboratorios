# LAB05 — Experimento em Software Real

Laboratório mais aberto do semestre: o trio escolhe o software real, a pergunta de
pesquisa, o caminho do estudo e o formato final do documento e da apresentação.

Enunciado completo: [enunciado_lab05.md](enunciado_lab05.md).

Divisão de tarefas da Sprint 1 (Lab05S01): [DIVISAO_SPRINT1.md](DIVISAO_SPRINT1.md).

## Decisão do grupo

- **Software:** API SGS do Banco Central do Brasil (dados abertos — real, em operação,
  alto impacto; ver evidências com números e fontes em
  [docs/evidencias_criterios.md](docs/evidencias_criterios.md)).
- **Caminho:** medir o serviço de fora, coletando a latência de requisições HTTP à API,
  no máximo 1 por segundo.
- **Pergunta de pesquisa:** o tempo de resposta da API varia entre horário comercial
  (09h–18h) e fora do horário comercial, em dias úteis?

> A decisão original (PostgreSQL 15×17 com `pgbench` em Docker) foi trocada em
> 2026-11-19 por falta de Docker/permissão de admin na máquina de coleta — ver o
> histórico em [docs/decisao_software_caminho.md](docs/decisao_software_caminho.md).

Detalhes (critérios, GQM, hipóteses, ameaças à validade, ética): [docs/decisao_software_caminho.md](docs/decisao_software_caminho.md).

## Status

- [x] Software escolhido (com evidências dos 3 critérios da seção 2a)
- [x] Pergunta de pesquisa e caminho(s) do estudo definidos
- [x] 7 categorias de pesquisa (primeira versão) (A) — ver [docs/categorias_pesquisa.md](docs/categorias_pesquisa.md)
- [x] Plano de coleta (B) — ver [docs/plano_coleta.md](docs/plano_coleta.md)
- [ ] Plano de análise (C) — pendente
- [x] Coleta piloto (B) — ver [dados/coleta_piloto.csv](dados/coleta_piloto.csv)

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| [docs/](docs/) | Decisões do grupo, plano de coleta, categorias de pesquisa, plano de análise |
| [scripts/](scripts/) | Código de coleta (`coletar_latencia_bcb.py`) |
| [dados/](dados/) | Dados coletados (piloto e completos) |
| `apresentacao/` | Slides ou outro material de apresentação (a criar) |

Link do repositório/GitHub Projects: `<preencher>`
