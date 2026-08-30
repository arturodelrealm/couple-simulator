import pytest

from rules_evaluator.errors import InvalidRuleError
from rules_evaluator.paths import parse_path, resolve_path


def test_resolve_nested_dict() -> None:
    context = {"state": {"finances": 55, "age": 30}}
    assert resolve_path(context, "state/finances") == 55


def test_resolve_missing_segment_returns_none() -> None:
    context = {"state": {"finances": 55}}
    assert resolve_path(context, "state/missing") is None


def test_resolve_list_index() -> None:
    context = {"items": [{"id": "first"}, {"id": "second"}]}
    assert resolve_path(context, "items/0/id") == "first"


def test_resolve_empty_path_raises() -> None:
    with pytest.raises(InvalidRuleError, match="non-empty string"):
        parse_path("")
