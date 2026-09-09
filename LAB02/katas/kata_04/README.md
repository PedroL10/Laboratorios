# K4 - Pontuacao de campeonato

**Nivel:** Medio

Implemente `rank_teams(matches)` em `solution.py`.

Cada partida e um dicionario com `home`, `away`, `home_score` e `away_score`. A funcao deve retornar uma lista de dicionarios com a classificacao final dos times.

Para cada time, calcule:

- `team`: nome do time;
- `points`: 3 pontos por vitoria, 1 por empate e 0 por derrota;
- `wins`: quantidade de vitorias;
- `goal_difference`: gols marcados menos gols sofridos;
- `goals_for`: total de gols marcados.

Ordene a classificacao por:

1. pontos, em ordem decrescente;
2. vitorias, em ordem decrescente;
3. saldo de gols, em ordem decrescente;
4. gols marcados, em ordem decrescente;
5. nome do time, em ordem alfabetica.

Regras:

- Uma lista vazia retorna `[]`.
- Um time nao pode jogar contra ele mesmo.
- Os placares sao inteiros maiores ou iguais a zero.
- Duas partidas entre os mesmos times sao permitidas.
- Nao altere a lista original.
- Nao use bibliotecas externas.

Exemplo:

```python
rank_teams([
    {"home": "A", "away": "B", "home_score": 2, "away_score": 0},
    {"home": "B", "away": "C", "home_score": 1, "away_score": 1},
])
# [
#   {"team": "A", "points": 3, "wins": 1, "goal_difference": 2, "goals_for": 2},
#   {"team": "B", "points": 1, "wins": 0, "goal_difference": -2, "goals_for": 1},
#   {"team": "C", "points": 1, "wins": 0, "goal_difference": 0, "goals_for": 1},
# ]
```

Execute os testes com:

```powershell
pytest -q
```
