import pytest

from solution import rank_teams


def test_awards_three_points_for_home_win():
    result = rank_teams([{"home": "A", "away": "B", "home_score": 2, "away_score": 0}])
    assert result == [
        {"team": "A", "points": 3, "wins": 1, "goal_difference": 2, "goals_for": 2},
        {"team": "B", "points": 0, "wins": 0, "goal_difference": -2, "goals_for": 0},
    ]


def test_awards_one_point_for_draw():
    result = rank_teams([{"home": "A", "away": "B", "home_score": 1, "away_score": 1}])
    assert result[0]["points"] == 1
    assert result[1]["points"] == 1


def test_awards_three_points_for_away_win():
    result = rank_teams([{"home": "A", "away": "B", "home_score": 0, "away_score": 1}])
    assert result[0]["team"] == "B"


def test_returns_empty_list_without_matches():
    assert rank_teams([]) == []


def test_uses_wins_as_first_tiebreaker_after_points():
    matches = [
        {"home": "A", "away": "B", "home_score": 1, "away_score": 0},
        {"home": "C", "away": "D", "home_score": 0, "away_score": 0},
    ]
    result = rank_teams(matches)
    assert result[0]["team"] == "A"


def test_uses_goal_difference_as_tiebreaker():
    matches = [
        {"home": "A", "away": "B", "home_score": 2, "away_score": 0},
        {"home": "C", "away": "D", "home_score": 1, "away_score": 0},
    ]
    result = rank_teams(matches)
    assert result[0]["team"] == "A"


def test_uses_team_name_for_complete_tie():
    matches = [{"home": "B", "away": "A", "home_score": 0, "away_score": 0}]
    result = rank_teams(matches)
    assert [item["team"] for item in result] == ["A", "B"]


def test_accumulates_multiple_matches():
    matches = [
        {"home": "A", "away": "B", "home_score": 2, "away_score": 0},
        {"home": "A", "away": "C", "home_score": 1, "away_score": 1},
    ]
    result = rank_teams(matches)
    assert result[0]["team"] == "A"
    assert result[0]["points"] == 4
    assert result[0]["wins"] == 1


def test_rejects_team_playing_against_itself():
    with pytest.raises((TypeError, ValueError)):
        rank_teams([{"home": "A", "away": "A", "home_score": 1, "away_score": 0}])


def test_rejects_negative_score():
    with pytest.raises((TypeError, ValueError)):
        rank_teams([{"home": "A", "away": "B", "home_score": -1, "away_score": 0}])
