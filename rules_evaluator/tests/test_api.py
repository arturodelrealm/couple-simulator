import pytest

from rules_evaluator import evaluate, evaluate_all


def test_evaluate_none_returns_true(minimal_context: dict) -> None:
    assert evaluate(None, minimal_context) is True


def test_evaluate_empty_dict_returns_true(minimal_context: dict) -> None:
    assert evaluate({}, minimal_context) is True


def test_evaluate_empty_all_returns_true(minimal_context: dict) -> None:
    assert evaluate({"type": "all", "items": []}, minimal_context) is True


def test_evaluate_empty_list_returns_true(minimal_context: dict) -> None:
    assert evaluate([], minimal_context) is True


def test_evaluate_all_empty_list_returns_true(minimal_context: dict) -> None:
    assert evaluate_all([], minimal_context) is True


def test_evaluate_all_requires_all_rules(minimal_context: dict) -> None:
    rule_pass = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 40,
    }
    rule_fail = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 100,
    }
    assert evaluate_all([rule_pass, rule_pass], minimal_context) is True
    assert evaluate_all([rule_pass, rule_fail], minimal_context) is False


def test_evaluate_rejects_non_dict_context(minimal_context: dict) -> None:
    with pytest.raises(TypeError, match="context must be a dict"):
        evaluate(None, [])  # type: ignore[arg-type]
