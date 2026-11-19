# Plano de coleta e coleta piloto (B — Instrumentação e Operação)

## Instrumento

Script: [scripts/coletar_latencia_bcb.py](../scripts/coletar_latencia_bcb.py).

Faz requisições HTTP GET à série 1 (dólar PTAX) da API SGS do Banco Central
(`api.bcb.gov.br`), medindo o tempo entre o envio e o recebimento da resposta
(latência ponta a ponta). Respeita um intervalo mínimo de 1 segundo entre
requisições (constante `INTERVALO_MINIMO_SEGUNDOS`), não usa autenticação e não
envia nem recebe nenhum dado pessoal.

Cada linha coletada registra: `timestamp`, `hora` (0–23), `periodo` (`comercial` se
09h–18h, senão `fora_comercial`), `latencia_ms`, `status_http` e `erro` (vazio em
caso de sucesso).

## Coleta piloto (rodada em 2026-11-19)

10 requisições em sequência, no horário comercial (13h). Resultado em
[dados/coleta_piloto.csv](../dados/coleta_piloto.csv):

- 10/10 requisições com status HTTP 200 (nenhuma falha).
- Latência entre ~112 ms e ~831 ms, com bastante variação mesmo dentro do mesmo
  minuto — já indica que o tamanho de amostra da coleta completa precisa ser maior
  que 10 por período para ter poder estatístico razoável (tarefa de C confirmar com
  base nisso).

O instrumento funcionou de ponta a ponta: nenhum ajuste de formato foi necessário.

## Plano para a coleta completa (Sprint 2)

A confirmar com o grupo antes da Sprint 2, mas a proposta inicial de B é:

- Rodar o script em pelo menos 2 dias úteis diferentes.
- Em cada dia, coletar ~30 amostras espalhadas pelo período comercial (09h–18h) e
  ~30 amostras espalhadas pelo período fora do comercial (ex.: madrugada, início da
  manhã, noite), chamando o script várias vezes ao longo do dia em vez de uma única
  rajada de 60 requisições seguidas (reduz o risco de medir só o estado da rede num
  instante específico).
- Guardar cada execução em `dados/coleta_<data>.csv` (o script já faz append se
  apontar pro mesmo arquivo dentro do mesmo dia) e depois consolidar os CSVs antes da
  análise de C.
- Repetir a checagem de `robots.txt` do domínio `api.bcb.gov.br` antes da coleta
  completa, por garantia.

## Comando usado

```bash
python coletar_latencia_bcb.py --n 10
```

Parâmetros: `--n` (nº de requisições) e `--saida` (caminho do CSV, padrão
`dados/coleta_piloto.csv`).
