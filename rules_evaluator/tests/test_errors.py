import pytest

from rules_evaluator import evaluate
from rules_evaluator.errors import (
    InvalidRuleError,
    UnknownOperatorError,
)
from rules_evaluator.nodes import MAX_ITEMS_PER_NODE, MAX_TREE_DEPTH


def test_unknown_node_type(minimal_context: dict) -> None:
    with pytest.raises(InvalidRuleError, match="unknown node type 'xor'"):
        evaluate({"type": "xor", "items": []}, minimal_context)


def test_unknown_operator(minimal_context: dict) -> None:
    with pytest.raises(UnknownOperatorError, match="unsupported operator 'bogus'"):
        evaluate(
            {
                "type": "compare",
                "path": "state/finances",
                "op": "bogus",
                "value": 40,
            },
            minimal_context,
        )


def test_compare_requires_value_or_value_getter(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 40,
        "value_getter": "thresholds/min_finances",
    }
    with pytest.raises(
        InvalidRuleError,
        match="exactly one of 'value' or 'value_getter'",
    ):
        evaluate(rule, minimal_context)


def test_compare_missing_value_and_value_getter(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
    }
    with pytest.raises(
        InvalidRuleError,
        match="exactly one of 'value' or 'value_getter'",
    ):
        evaluate(rule, minimal_context)


def test_compare_missing_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "op": "gte",
        "value": 40,
    }
    with pytest.raises(InvalidRuleError, match="missing 'path'"):
        evaluate(rule, minimal_context)


def test_compare_empty_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "",
        "op": "gte",
        "value": 40,
    }
    with pytest.raises(InvalidRuleError, match="non-empty string"):
        evaluate(rule, minimal_context)


def test_not_requires_single_child(minimal_context: dict) -> None:
    with pytest.raises(InvalidRuleError, match="exactly one child"):
        evaluate({"type": "not", "items": []}, minimal_context)


def test_all_requires_list_items(minimal_context: dict) -> None:
    with pytest.raises(InvalidRuleError, match="'items' must be a list"):
        evaluate({"type": "all", "items": "nope"}, minimal_context)


def test_max_depth_exceeded(minimal_context: dict) -> None:
    node: dict = {
        "type": "not",
        "items": [
            {
                "type": "compare",
                "path": "state/age",
                "op": "gte",
                "value": 18,
            }
        ],
    }
    for _ in range(MAX_TREE_DEPTH + 2):
        node = {"type": "not", "items": [node]}

    with pytest.raises(InvalidRuleError, match="exceeds maximum depth"):
        evaluate(node, minimal_context)


def test_max_items_exceeded(minimal_context: dict) -> None:
    child = {
        "type": "compare",
        "path": "state/age",
        "op": "gte",
        "value": 18,
    }
    rule = {
        "type": "all",
        "items": [child] * (MAX_ITEMS_PER_NODE + 1),
    }
    with pytest.raises(InvalidRuleError, match="exceeds maximum size"):
        evaluate(rule, minimal_context)


def test_invalid_tags_context_returns_false(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "tags",
        "op": "contains",
        "value": "financial",
    }
    context = {**minimal_context, "tags": 42}
    assert evaluate(rule, context) is False
