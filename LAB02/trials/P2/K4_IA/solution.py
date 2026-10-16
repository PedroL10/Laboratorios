def rank_teams(matches):
    stats = {}

    def team(name):
        return stats.setdefault(
            name,
            {"team": name, "points": 0, "wins": 0, "goal_difference": 0, "goals_for": 0},
        )

    for match in matches:
        home, away = match["home"], match["away"]
        home_score, away_score = match["home_score"], match["away_score"]
        if home == away:
            raise ValueError("a team cannot play against itself")
        if home_score < 0 or away_score < 0:
            raise ValueError("scores must be non-negative")

        home_team = team(home)
        away_team = team(away)

        home_team["goals_for"] += home_score
        away_team["goals_for"] += away_score
        home_team["goal_difference"] += home_score - away_score
        away_team["goal_difference"] += away_score - home_score

        if home_score > away_score:
            home_team["points"] += 3
            home_team["wins"] += 1
        elif away_score > home_score:
            away_team["points"] += 3
            away_team["wins"] += 1
        else:
            home_team["points"] += 1
            away_team["points"] += 1

    ranking = list(stats.values())
    ranking.sort(
        key=lambda t: (
            -t["points"],
            -t["wins"],
            -t["goal_difference"],
            -t["goals_for"],
            t["team"],
        )
    )
    return ranking