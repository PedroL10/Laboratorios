"""
Lab01S02 - Sprint 2: Paginação + Exportação CSV
Coleta 1000 repositórios populares do GitHub usando paginação
e exporta os dados para um arquivo CSV.
"""

import os
import requests
import json
import time
import csv
from datetime import datetime
from dotenv import load_dotenv
from queries import QUERY_PAGINADA

# 1. Carrega variáveis de ambiente
load_dotenv()

# 2. Configurações
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
URL = 'https://api.github.com/graphql'
TOTAL_REPOS_DESEJADO = 1000
REPOS_POR_PAGINA = 10

# 3. Verifica se o token existe
if not GITHUB_TOKEN:
    raise ValueError("Token do GitHub não encontrado. Verifique o arquivo .env")

# 4. Define cabeçalhos da requisição
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}


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
                print(f"    Rate limit atingido. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue
            
            # Erros do servidor (5xx) incluindo 502 - tenta novamente
            if response.status_code >= 500:
                tempo_espera = delay_inicial * tentativa
                print(f"    Erro do servidor ({response.status_code}). Tentativa {tentativa}/{max_tentativas}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
                continue
            
            # Erros 4xx (exceto rate limit) - não faz retry
            print(f"    Erro na requisição: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout:
            print(f"    Timeout na tentativa {tentativa}/{max_tentativas}")
        except requests.exceptions.ConnectionError:
            print(f"    Erro de conexão na tentativa {tentativa}/{max_tentativas}")
        except requests.exceptions.RequestException as e:
            print(f"    Erro na requisição: {e}")
        
        # Espera antes da próxima tentativa
        if tentativa < max_tentativas:
            tempo_espera = delay_inicial * tentativa
            time.sleep(tempo_espera)
    
    print(f"    Todas as {max_tentativas} tentativas falharam.")
    return None


def calcular_idade_dias(data_criacao):
    """Calcula a idade do repositório em dias."""
    try:
        criacao = datetime.strptime(data_criacao, "%Y-%m-%dT%H:%M:%SZ")
        hoje = datetime.now()
        return (hoje - criacao).days
    except:
        return None


def calcular_dias_desde_atualizacao(data_atualizacao):
    """Calcula quantos dias desde a última atualização."""
    try:
        atualizacao = datetime.strptime(data_atualizacao, "%Y-%m-%dT%H:%M:%SZ")
        hoje = datetime.now()
        return (hoje - atualizacao).days
    except:
        return None


def calcular_razao_issues_fechadas(issues_total, issues_fechadas):
    """Calcula a razão de issues fechadas."""
    if issues_total and issues_total > 0:
        return round(issues_fechadas / issues_total, 4)
    return None


def processar_repositorio(repo):
    """Processa os dados de um repositório para formato tabular."""
    
    # Extrai dados básicos
    nome = repo.get('nameWithOwner', '')
    criado_em = repo.get('createdAt', '')
    atualizado_em = repo.get('updatedAt', '')
    estrelas = repo.get('stargazerCount', 0)
    
    # Linguagem primária
    linguagem_obj = repo.get('primaryLanguage')
    linguagem = linguagem_obj.get('name') if linguagem_obj else None
    
    # Métricas
    prs_merged = repo.get('pullRequests', {}).get('totalCount', 0)
    releases = repo.get('releases', {}).get('totalCount', 0)
    issues_total = repo.get('issues', {}).get('totalCount', 0)
    issues_fechadas = repo.get('closedIssues', {}).get('totalCount', 0)
    
    # Métricas calculadas
    idade_dias = calcular_idade_dias(criado_em)
    dias_desde_atualizacao = calcular_dias_desde_atualizacao(atualizado_em)
    razao_issues_fechadas = calcular_razao_issues_fechadas(issues_total, issues_fechadas)
    
    return {
        'nome': nome,
        'criado_em': criado_em,
        'atualizado_em': atualizado_em,
        'estrelas': estrelas,
        'linguagem': linguagem,
        'prs_merged': prs_merged,
        'releases': releases,
        'issues_total': issues_total,
        'issues_fechadas': issues_fechadas,
        'idade_dias': idade_dias,
        'dias_desde_atualizacao': dias_desde_atualizacao,
        'razao_issues_fechadas': razao_issues_fechadas
    }


def coletar_repositorios_paginado(total_desejado=1000):
    """
    Coleta repositórios usando paginação.
    
    Args:
        total_desejado: Número total de repositórios a coletar
    
    Returns:
        Lista de repositórios processados
    """
    todos_repositorios = []
    cursor = None
    pagina = 1
    total_paginas = total_desejado // REPOS_POR_PAGINA
    
    print(f"\n{'='*60}")
    print(f"Iniciando coleta de {total_desejado} repositórios com paginação")
    print(f"Páginas estimadas: {total_paginas} ({REPOS_POR_PAGINA} repos/página)")
    print(f"{'='*60}\n")
    
    while len(todos_repositorios) < total_desejado:
        print(f"[Página {pagina}/{total_paginas}] Coletando repositórios {len(todos_repositorios)+1}-{len(todos_repositorios)+REPOS_POR_PAGINA}...")
        
        variables = {"cursor": cursor}
        response = fazer_requisicao_com_retry(QUERY_PAGINADA, variables)
        
        if response is None:
            print(f"  ✗ Falha na página {pagina}. Continuando com {len(todos_repositorios)} repositórios coletados.")
            break
        
        if response.status_code != 200:
            print(f"  ✗ Erro HTTP {response.status_code}")
            break
        
        dados = response.json()
        
        if "errors" in dados:
            print(f"  ✗ Erro GraphQL: {dados['errors']}")
            break
        
        if "data" not in dados:
            print(f"  ✗ Resposta inesperada")
            break
        
        search_data = dados['data']['search']
        repos_pagina = search_data['nodes']
        
        # Processa cada repositório
        for repo in repos_pagina:
            repo_processado = processar_repositorio(repo)
            todos_repositorios.append(repo_processado)
        
        print(f"  ✓ Coletados {len(repos_pagina)} repositórios (total: {len(todos_repositorios)})")
        
        # Verifica se há mais páginas
        page_info = search_data['pageInfo']
        if not page_info['hasNextPage']:
            print("\n  ⚠ Não há mais páginas disponíveis.")
            break
        
        cursor = page_info['endCursor']
        pagina += 1
        
        # Pausa entre requisições para evitar rate limit
        if len(todos_repositorios) < total_desejado:
            time.sleep(2)
    
    return todos_repositorios[:total_desejado]


def exportar_para_csv(repositorios, nome_arquivo='repositorios.csv'):
    """
    Exporta os repositórios para um arquivo CSV.
    
    Args:
        repositorios: Lista de repositórios processados
        nome_arquivo: Nome do arquivo CSV de saída
    """
    if not repositorios:
        print("Nenhum repositório para exportar.")
        return
    
    # Define as colunas do CSV
    colunas = [
        'nome',
        'criado_em',
        'atualizado_em',
        'estrelas',
        'linguagem',
        'prs_merged',
        'releases',
        'issues_total',
        'issues_fechadas',
        'idade_dias',
        'dias_desde_atualizacao',
        'razao_issues_fechadas'
    ]
    
    # Escreve o CSV
    with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(repositorios)
    
    print(f"\n✓ Dados exportados para: {nome_arquivo}")
    print(f"  Total de linhas: {len(repositorios)}")


def exibir_estatisticas(repositorios):
    """Exibe estatísticas básicas dos dados coletados."""
    
    if not repositorios:
        return
    
    print(f"\n{'='*60}")
    print("ESTATÍSTICAS DOS DADOS COLETADOS")
    print(f"{'='*60}")
    
    # Total de repositórios
    total = len(repositorios)
    print(f"\nTotal de repositórios: {total}")
    
    # Estatísticas de estrelas
    estrelas = [r['estrelas'] for r in repositorios if r['estrelas']]
    if estrelas:
        print(f"\nEstrelas:")
        print(f"  Máximo: {max(estrelas):,}")
        print(f"  Mínimo: {min(estrelas):,}")
        print(f"  Média: {sum(estrelas)/len(estrelas):,.0f}")
    
    # Estatísticas de idade
    idades = [r['idade_dias'] for r in repositorios if r['idade_dias']]
    if idades:
        print(f"\nIdade (dias):")
        print(f"  Máximo: {max(idades):,}")
        print(f"  Mínimo: {min(idades):,}")
        print(f"  Média: {sum(idades)/len(idades):,.0f}")
        print(f"  Média (anos): {sum(idades)/len(idades)/365:.1f}")
    
    # Linguagens mais comuns
    linguagens = {}
    for r in repositorios:
        lang = r['linguagem'] or 'Não especificada'
        linguagens[lang] = linguagens.get(lang, 0) + 1
    
    print(f"\nTop 10 Linguagens:")
    for i, (lang, count) in enumerate(sorted(linguagens.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        porcentagem = count / total * 100
        print(f"  {i:2}. {lang}: {count} ({porcentagem:.1f}%)")
    
    # PRs Merged
    prs = [r['prs_merged'] for r in repositorios if r['prs_merged'] is not None]
    if prs:
        print(f"\nPull Requests Merged:")
        print(f"  Total: {sum(prs):,}")
        print(f"  Média por repo: {sum(prs)/len(prs):,.0f}")
    
    # Razão de issues fechadas
    razoes = [r['razao_issues_fechadas'] for r in repositorios if r['razao_issues_fechadas'] is not None]
    if razoes:
        print(f"\nRazão de Issues Fechadas:")
        print(f"  Média: {sum(razoes)/len(razoes):.2%}")


def main():
    """Função principal."""
    
    print("\n" + "="*60)
    print("LAB01S02 - Sprint 2: Paginação + Exportação CSV")
    print("="*60)
    
    # Coleta os repositórios
    repositorios = coletar_repositorios_paginado(TOTAL_REPOS_DESEJADO)
    
    if not repositorios:
        print("\n✗ Nenhum repositório foi coletado.")
        exit(1)
    
    print(f"\n{'='*60}")
    print(f"COLETA FINALIZADA: {len(repositorios)} repositórios")
    print(f"{'='*60}")
    
    # Exporta para CSV
    exportar_para_csv(repositorios, 'repositorios.csv')
    
    # Exibe estatísticas
    exibir_estatisticas(repositorios)
    
    # Exibe amostra dos dados
    print(f"\n{'='*60}")
    print("AMOSTRA DOS DADOS (primeiros 5 repositórios)")
    print(f"{'='*60}\n")
    
    for i, repo in enumerate(repositorios[:5], 1):
        print(f"--- Repositório {i} ---")
        print(json.dumps(repo, indent=2, ensure_ascii=False, default=str))
        print()


if __name__ == "__main__":
    main()
