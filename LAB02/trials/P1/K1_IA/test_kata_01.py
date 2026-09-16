import pytest

from solution import summarize_readings


def test_counts_readings_at_or_above_minimum():
    assert summarize_readings([10, 12, 8, 12], 10) == {
        "count": 3,
        "average": 10.5,
        "maximum": 12,
    }


def test_handles_empty_readings():
    assert summarize_readings([], 10) == {
        "count": 0,
        "average": 0.0,
        "maximum": None,
    }


def test_handles_negative_values():
    assert summarize_readings([-5, -2, -8], -5) == {
        "count": 2,
        "average": -5.0,
        "maximum": -2,
    }


def test_includes_values_equal_to_minimum():
    assert summarize_readings([3, 3, 3], 3)["count"] == 3


def test_returns_two_decimal_average():
    assert summarize_readings([1, 2, 2], 0)["average"] == 1.67


def test_returns_maximum_for_unsorted_input():
    assert summarize_readings([4, 1, 9, 2], 0)["maximum"] == 9


def test_does_not_mutate_input():
    readings = [3, 1, 2]
    summarize_readings(readings, 2)
    assert readings == [3, 1, 2]


def test_counts_no_values_when_minimum_is_above_all():
    assert summarize_readings([1, 2, 3], 4)["count"] == 0


def test_accepts_zero_values():
    assert summarize_readings([0, 0, 1], 0)["count"] == 3


def test_raises_for_non_list_input():
    with pytest.raises((TypeError, ValueError)):
        summarize_readings(None, 1)
