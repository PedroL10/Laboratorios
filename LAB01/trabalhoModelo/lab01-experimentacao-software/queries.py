QUERY_100_REPOS = """
query {
  search(
    query: "stars:>10000 sort:stars-desc",
    type: REPOSITORY,
    first: 100
  ) {
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        updatedAt
        primaryLanguage { name }
        pullRequests(states: MERGED) { totalCount }
        releases { totalCount }
        issues { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
      }
    }
  }
}
"""

# Query parametrizada para busca por faixa de estrelas
QUERY_POR_FAIXA = """
query($queryStr: String!) {
  search(
    query: $queryStr,
    type: REPOSITORY,
    first: 10
  ) {
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        updatedAt
        stargazerCount
        primaryLanguage { name }
        pullRequests(states: MERGED) { totalCount }
        releases { totalCount }
        issues { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
      }
    }
  }
}
"""

# Query com paginação para Sprint 2 (1000 repositórios)
QUERY_PAGINADA = """
query($cursor: String) {
  search(
    query: "stars:>10000 sort:stars-desc",
    type: REPOSITORY,
    first: 10,
    after: $cursor
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        createdAt
        updatedAt
        stargazerCount
        primaryLanguage { name }
        pullRequests(states: MERGED) { totalCount }
        releases { totalCount }
        issues { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
      }
    }
  }
}
"""