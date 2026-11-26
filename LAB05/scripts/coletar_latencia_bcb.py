"""Coleta de latência da API SGS do Banco Central (ver docs/plano_coleta.md).

Mede o tempo de resposta (ponta a ponta) de requisições GET simples à série 1 (dólar
PTAX) da API pública do BCB, respeitando o limite de 1 requisição por segundo exigido
pelo enunciado do LAB05. Não coleta nenhum dado pessoal: a série consultada é um
indicador econômico agregado e público.

Cada execução do script é uma **rodada**: N requisições seguidas, identificadas pela
mesma coluna `rodada`. A análise usa a rodada como unidade (por exemplo, a mediana de
cada rodada), porque requisições do mesmo minuto não são independentes.

Os horários são sempre registrados no fuso de Brasília, mesmo quando o script roda em
uma máquina em UTC (como o GitHub Actions).

Uso:
    python coletar_latencia_bcb.py --n 5 --saida ../dados/coleta.csv --origem local
"""

import argparse
import csv
import datetime as dt
import pathlib
import time
import urllib.error
import urllib.request

try:
    from zoneinfo import ZoneInfo

    FUSO = ZoneInfo("America/Sao_Paulo")
except Exception:  # sem base de fusos instalada: Brasília não tem horário de verão desde 2019
    FUSO = dt.timezone(dt.timedelta(hours=-3), "BRT")

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
USER_AGENT = "lab05-latencia (estudo academico; 1 req/s no maximo)"
INTERVALO_MINIMO_SEGUNDOS = 1.0
TIMEOUT_SEGUNDOS = 10
HORA_INICIO_COMERCIAL = 9
HORA_FIM_COMERCIAL = 18
CAMPOS = [
    "rodada",
    "timestamp",
    "data",
    "dia_semana",
    "hora",
    "periodo",
    "latencia_ms",
    "status_http",
    "bytes",
    "erro",
    "origem",
]


def agora() -> dt.datetime:
    """Momento atual no fuso de Brasília."""
    return dt.datetime.now(FUSO)


def periodo_do_horario(hora: int) -> str:
    if HORA_INICIO_COMERCIAL <= hora < HORA_FIM_COMERCIAL:
        return "comercial"
    return "fora_comercial"


def medir_uma_requisicao(rodada: str, origem: str) -> dict:
    momento = agora()
    requisicao = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    status = None
    tamanho = None
    erro = ""
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:
            status = resposta.status
            tamanho = len(resposta.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        erro = str(exc)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        erro = str(exc)
    latencia_ms = (time.perf_counter() - inicio) * 1000
    return {
        "rodada": rodada,
        "timestamp": momento.isoformat(timespec="seconds"),
        "data": momento.date().isoformat(),
        "dia_semana": momento.weekday(),  # 0 = segunda ... 6 = domingo
        "hora": momento.hour,
        "periodo": periodo_do_horario(momento.hour),
        "latencia_ms": round(latencia_ms, 2),
        "status_http": status,
        "bytes": tamanho,
        "erro": erro,
        "origem": origem,
    }


def coletar(n: int, caminho_saida: pathlib.Path, origem: str) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_existe = caminho_saida.exists() and caminho_saida.stat().st_size > 0
    rodada = agora().isoformat(timespec="seconds")
    with caminho_saida.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        if not arquivo_existe:
            escritor.writeheader()
        for i in range(n):
            amostra = medir_uma_requisicao(rodada, origem)
            escritor.writerow(amostra)
            arquivo.flush()
            print(f"[{i + 1}/{n}] {amostra['latencia_ms']} ms, status {amostra['status_http']}")
            if i < n - 1:
                time.sleep(INTERVALO_MINIMO_SEGUNDOS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=5, help="Número de requisições da rodada")
    parser.add_argument(
        "--saida",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "dados" / "coleta.csv",
        help="Caminho do CSV de saída (acrescenta linhas se já existir)",
    )
    parser.add_argument(
        "--origem",
        default="local",
        help="De onde a coleta foi feita, por exemplo github-actions ou local",
    )
    args = parser.parse_args()
    coletar(args.n, args.saida, args.origem)
