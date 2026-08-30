import pytest

from rules_evaluator.operators import apply_operator


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (40, 40, True),
        (40, 41, False),
        ("yes", "yes", True),
        (None, None, True),
        (None, 1, False),
        (1, None, False),
    ],
)
def test_eq(left: object, right: object, expected: bool) -> None:
    assert apply_operator("eq", left, right) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (40, 41, True),
        (40, 40, False),
        (None, 1, True),
        (None, None, False),
    ],
)
def test_neq(left: object, right: object, expected: bool) -> None:
    assert apply_operator("neq", left, right) is expected


@pytest.mark.parametrize(
    ("op", "left", "right", "expected"),
    [
        ("gt", 41, 40, True),
        ("gt", 40, 40, False),
        ("gte", 40, 40, True),
        ("lt", 39, 40, True),
        ("lte", 40, 40, True),
    ],
)
def test_ordering(op: str, left: int, right: int, expected: bool) -> None:
    assert apply_operator(op, left, right) is expected


def test_in_operator() -> None:
    assert apply_operator("in", "beach", ["beach", "mountain"]) is True
    assert apply_operator("in", "city", ["beach", "mountain"]) is False


def test_in_with_non_iterable_right_returns_false() -> None:
    assert apply_operator("in", "a", 42) is False


def test_in_with_string_right_returns_false() -> None:
    assert apply_operator("in", "a", "abc") is False


def test_incomparable_types_return_false() -> None:
    assert apply_operator("gt", "40", 40) is False


def test_contains_operator() -> None:
    assert apply_operator("contains", ["beach", "mountain"], "beach") is True
    assert apply_operator("contains", ["beach"], "city") is False
    assert apply_operator("contains", 42, "city") is False
