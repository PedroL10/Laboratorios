"""
Lab01S01: Consulta graphql para 100 repositórios 
(com todos os dados/métricas necessários para responder
as RQs) + requisição automática 
"""

import os
import requests
import json
import time
from dotenv import load_dotenv
from queries import QUERY_POR_FAIXA

# 1. Carrega variáveis de ambiente
load_dotenv()

# 2. Obtém token do GitHub
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
URL = 'https://api.github.com/graphql'

# 3. Verifica se o token existe
if not GITHUB_TOKEN:
    raise ValueError("Token do GitHub não encontrado. Verifique o arquivo .env")

# 4. Define cabeçalhos da requisição
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

# 5. Função de requisição com retry
def fazer_requisicao_com_retry(query, variables=None, max_tentativas=10, delay_inicial=5):
    """
    Faz requisição à API do GitHub com retry automático.
    
    Args:
        query: Query GraphQL a ser executada
        variables: Variáveis da query
        max_tentativas: Número máximo de tentativas
        delay_inicial: Tempo inicial de espera entre tentativas (em segundos)
    
    Returns:
        Response object em caso de sucesso, None se todas as tentativas falharem
    """
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
        
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"  Tentativa {tentativa}/{max_tentativas}...")
            response = requests.post(
                URL,
                json=payload,
                headers=headers,
                timeout=120
            )
            
            # Sucesso
            if response.status_code == 200:
                return response
            
            # Rate limit - espera mais tempo
            if response.status_code == 403 or response.status_code == 429:
                tempo_espera = delay_inicial * (2 ** tentativa)
                print(f"  Rate limit atingido. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue
            
            # Erros do servidor (5xx) incluindo 502 - tenta novamente
            if response.status_code >= 500:
                tempo_espera = delay_inicial * tentativa  # Linear para 502
                print(f"  Erro do servidor ({response.status_code}). Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue
            
            # Erros 4xx (exceto rate limit) - não faz retry
            print(f"  Erro na requisição: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout:
            print(f"  Timeout na tentativa {tentativa}")
        except requests.exceptions.ConnectionError:
            print(f"  Erro de conexão na tentativa {tentativa}")
        except requests.exceptions.RequestException as e:
            print(f"  Erro na requisição: {e}")
        
        # Espera antes da próxima tentativa
        if tentativa < max_tentativas:
            tempo_espera = delay_inicial * tentativa
            print(f"  Aguardando {tempo_espera}s antes da próxima tentativa...")
            time.sleep(tempo_espera)
    
    print(f"  Todas as {max_tentativas} tentativas falharam.")
    return None


# 6. Faixas de estrelas para dividir a busca (sem paginação)
# Cada faixa busca 10 repos, totalizando 100
FAIXAS_ESTRELAS = [
    "stars:>=200000",      # Top repos (200k+)
    "stars:150000..199999",
    "stars:120000..149999",
    "stars:100000..119999",
    "stars:85000..99999",
    "stars:70000..84999",
    "stars:60000..69999",
    "stars:50000..59999",
    "stars:45000..49999",
    "stars:40000..44999",
]

print("Iniciando busca de 100 repositórios em lotes por faixa de estrelas...")
print("(Sem paginação - usando filtros diferentes para cada lote)\n")

todos_repositorios = []

for i, faixa in enumerate(FAIXAS_ESTRELAS, 1):
    query_str = f"{faixa} sort:stars-desc"
    print(f"\n[Lote {i}/10] Buscando: {faixa}")
    
    response = fazer_requisicao_com_retry(
        QUERY_POR_FAIXA, 
        variables={"queryStr": query_str}
    )
    
    if response is None:
        print(f"  ✗ Falha no lote {i}. Continuando...")
        continue
    
    if response.status_code != 200:
        print(f"  ✗ Erro HTTP {response.status_code}")
        continue
    
    dados = response.json()
    
    if "errors" in dados:
        print(f"  ✗ Erro GraphQL: {dados['errors']}")
        continue
    
    if "data" not in dados:
        print(f"  ✗ Resposta inesperada")
        continue
    
    repos_lote = dados['data']['search']['nodes']
    todos_repositorios.extend(repos_lote)
    
    print(f"  ✓ Coletados {len(repos_lote)} repositórios (total: {len(todos_repositorios)})")
    
    # Pausa entre lotes para evitar rate limit
    if i < len(FAIXAS_ESTRELAS):
        print("  Aguardando 2s antes do próximo lote...")
        time.sleep(2)

# 7. Exibe resultado
print(f"\n{'='*50}")
print(f"Total de repositórios coletados: {len(todos_repositorios)}")
print(f"{'='*50}\n")

if todos_repositorios:
    print("Todos os repositórios coletados:")
    for i, repo in enumerate(todos_repositorios, 1):
        print(f"\n--- Repositório {i} ---")
        print(json.dumps(repo, indent=2, ensure_ascii=False))
else:
    print("Nenhum repositório foi coletado.")
    exit(1)