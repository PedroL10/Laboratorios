import pytest

from solution import validate_tags


def test_accepts_matching_single_tag():
    assert validate_tags("[card]texto[/card]") is True


def test_accepts_nested_tags():
    assert validate_tags("[a][b]x[/b][/a]") is True


def test_rejects_wrong_nesting_order():
    assert validate_tags("[a][b][/a][/b]") is False


def test_accepts_plain_text():
    assert validate_tags("texto sem etiquetas") is True


def test_accepts_empty_text():
    assert validate_tags("") is True


def test_rejects_unclosed_tag():
    assert validate_tags("[card]texto") is False


def test_rejects_closing_tag_without_opening():
    assert validate_tags("[/card]") is False


def test_rejects_mismatched_tag_names():
    assert validate_tags("[card]texto[/box]") is False


def test_rejects_invalid_tag_name():
    assert validate_tags("[Card]texto[/Card]") is False


def test_rejects_stray_bracket():
    assert validate_tags("texto [card") is False


def test_raises_for_non_string_input():
    with pytest.raises((TypeError, ValueError)):
        validate_tags(None)
