def rank_teams(matches):
    if not isinstance(matches, list):
        raise TypeError("matches must be a list")

    teams = {}

    for match in matches:
        home = match["home"]
        away = match["away"]
        home_score = match["home_score"]
        away_score = match["away_score"]

        if home == away:
            raise ValueError("a team cannot play against itself")

        if (
            not isinstance(home_score, int)
            or isinstance(home_score, bool)
            or not isinstance(away_score, int)
            or isinstance(away_score, bool)
        ):
            raise TypeError("scores must be integers")

        if home_score < 0 or away_score < 0:
            raise ValueError("scores cannot be negative")

        if home not in teams:
            teams[home] = {
                "team": home,
                "points": 0,
                "wins": 0,
                "goal_difference": 0,
                "goals_for": 0,
            }

        if away not in teams:
            teams[away] = {
                "team": away,
                "points": 0,
                "wins": 0,
                "goal_difference": 0,
                "goals_for": 0,
            }

        teams[home]["goals_for"] += home_score
        teams[away]["goals_for"] += away_score

        teams[home]["goal_difference"] += home_score - away_score
        teams[away]["goal_difference"] += away_score - home_score

        if home_score > away_score:
            teams[home]["points"] += 3
            teams[home]["wins"] += 1

        elif away_score > home_score:
            teams[away]["points"] += 3
            teams[away]["wins"] += 1

        else:
            teams[home]["points"] += 1
            teams[away]["points"] += 1

    result = list(teams.values())

    result.sort(
        key=lambda team: (
            -team["points"],
            -team["wins"],
            -team["goal_difference"],
            -team["goals_for"],
            team["team"],
        )
    )

    return result