import pytest

from solution import delivery_windows


def test_counts_overlapping_windows_in_one_zone():
    deliveries = [
        {"start": 1, "end": 4, "zone": "sul"},
        {"start": 2, "end": 3, "zone": "sul"},
        {"start": 4, "end": 6, "zone": "sul"},
    ]
    assert delivery_windows(deliveries) == {"sul": 2}


def test_separate_zones_do_not_interfere():
    deliveries = [
        {"start": 1, "end": 5, "zone": "norte"},
        {"start": 1, "end": 5, "zone": "sul"},
    ]
    assert delivery_windows(deliveries) == {"norte": 1, "sul": 1}


def test_reuses_window_when_start_equals_previous_end():
    deliveries = [
        {"start": 1, "end": 3, "zone": "centro"},
        {"start": 3, "end": 5, "zone": "centro"},
    ]
    assert delivery_windows(deliveries) == {"centro": 1}


def test_returns_empty_dictionary_for_no_deliveries():
    assert delivery_windows([]) == {}


def test_returns_zones_in_alphabetical_order():
    result = delivery_windows([
        {"start": 1, "end": 2, "zone": "sul"},
        {"start": 1, "end": 2, "zone": "norte"},
    ])
    assert list(result) == ["norte", "sul"]


def test_finds_peak_overlap_among_many_intervals():
    deliveries = [
        {"start": 1, "end": 10, "zone": "oeste"},
        {"start": 2, "end": 8, "zone": "oeste"},
        {"start": 3, "end": 7, "zone": "oeste"},
        {"start": 7, "end": 9, "zone": "oeste"},
    ]
    assert delivery_windows(deliveries) == {"oeste": 3}


def test_handles_unsorted_deliveries():
    deliveries = [
        {"start": 5, "end": 7, "zone": "sul"},
        {"start": 1, "end": 6, "zone": "sul"},
    ]
    assert delivery_windows(deliveries) == {"sul": 2}


def test_rejects_zero_length_delivery():
    with pytest.raises((TypeError, ValueError)):
        delivery_windows([{"start": 2, "end": 2, "zone": "sul"}])


def test_rejects_missing_zone():
    with pytest.raises((TypeError, ValueError, KeyError)):
        delivery_windows([{"start": 1, "end": 2}])


def test_does_not_mutate_input():
    deliveries = [{"start": 1, "end": 2, "zone": "sul"}]
    original = [item.copy() for item in deliveries]
    delivery_windows(deliveries)
    assert deliveries == original
