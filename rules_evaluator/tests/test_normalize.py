import pytest

from rules_evaluator.errors import InvalidRuleError
from rules_evaluator.normalize import normalize_rule


def test_normalize_none() -> None:
    assert normalize_rule(None) is None


def test_normalize_empty_dict() -> None:
    assert normalize_rule({}) is None


def test_normalize_empty_list() -> None:
    assert normalize_rule([]) is None


def test_normalize_empty_all() -> None:
    assert normalize_rule({"type": "all", "items": []}) is None


def test_normalize_flat_list() -> None:
    child = {
        "type": "compare",
        "path": "state/age",
        "op": "gte",
        "value": 18,
    }
    result = normalize_rule([child, child])
    assert result == {"type": "all", "items": [child, child]}


def test_normalize_single_item_list_flattens() -> None:
    child = {
        "type": "compare",
        "path": "state/age",
        "op": "gte",
        "value": 18,
    }
    assert normalize_rule([child]) == child


def test_normalize_all_with_empty_children() -> None:
    child = {
        "type": "compare",
        "path": "state/age",
        "op": "gte",
        "value": 18,
    }
    result = normalize_rule({"type": "all", "items": [None, {}, child]})
    assert result == child


def test_normalize_dict_without_type_raises() -> None:
    with pytest.raises(InvalidRuleError, match="missing 'type'"):
        normalize_rule({"path": "state/finances"})


def test_normalize_invalid_type_raises() -> None:
    with pytest.raises(InvalidRuleError, match="must be a dict"):
        normalize_rule(42)  # type: ignore[arg-type]
