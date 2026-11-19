"""Coleta de latência da API SGS do Banco Central (dados/decisao_software_caminho.md).

Mede o tempo de resposta (ponta a ponta) de requisições GET simples à série 1 (dólar
PTAX) da API pública do BCB, respeitando o limite de 1 requisição por segundo exigido
pelo enunciado do LAB05. Não coleta nenhum dado pessoal: a série consultada é um
indicador econômico agregado e público.

Uso:
    python coletar_latencia_bcb.py --n 10 --saida ../dados/coleta_piloto.csv
"""

import argparse
import csv
import datetime as dt
import pathlib
import time
import urllib.error
import urllib.request

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
INTERVALO_MINIMO_SEGUNDOS = 1.0
HORA_INICIO_COMERCIAL = 9
HORA_FIM_COMERCIAL = 18


def periodo_do_horario(hora: int) -> str:
    if HORA_INICIO_COMERCIAL <= hora < HORA_FIM_COMERCIAL:
        return "comercial"
    return "fora_comercial"


def medir_uma_requisicao() -> dict:
    inicio = time.perf_counter()
    timestamp = dt.datetime.now()
    status = None
    erro = ""
    try:
        with urllib.request.urlopen(URL, timeout=10) as resposta:
            status = resposta.status
            resposta.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        erro = str(exc)
    except urllib.error.URLError as exc:
        erro = str(exc)
    fim = time.perf_counter()
    latencia_ms = (fim - inicio) * 1000
    return {
        "timestamp": timestamp.isoformat(timespec="seconds"),
        "hora": timestamp.hour,
        "periodo": periodo_do_horario(timestamp.hour),
        "latencia_ms": round(latencia_ms, 2),
        "status_http": status,
        "erro": erro,
    }


def coletar(n: int, caminho_saida: pathlib.Path) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_existe = caminho_saida.exists()
    with caminho_saida.open("a", newline="", encoding="utf-8") as arquivo:
        campos = ["timestamp", "hora", "periodo", "latencia_ms", "status_http", "erro"]
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        if not arquivo_existe:
            escritor.writeheader()
        for i in range(n):
            amostra = medir_uma_requisicao()
            escritor.writerow(amostra)
            arquivo.flush()
            print(f"[{i + 1}/{n}] {amostra}")
            if i < n - 1:
                time.sleep(INTERVALO_MINIMO_SEGUNDOS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=10, help="Número de requisições")
    parser.add_argument(
        "--saida",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "dados" / "coleta_piloto.csv",
        help="Caminho do CSV de saída (append)",
    )
    args = parser.parse_args()
    coletar(args.n, args.saida)
