"""Resolve compare nodes against an evaluation context using paths."""

from __future__ import annotations

from typing import Any

from rules_evaluator.errors import InvalidRuleError
from rules_evaluator.operators import apply_operator
from rules_evaluator.paths import require_path_field, resolve_path


def _validate_compare_node(node: dict[str, Any], rule_path: str) -> None:
    require_path_field(node, "path", rule_path)

    if "op" not in node:
        msg = f"missing 'op' in compare node at {rule_path}"
        raise InvalidRuleError(msg)

    has_value = "value" in node
    has_value_getter = "value_getter" in node
    if has_value == has_value_getter:
        msg = (
            f"compare node must include exactly one of 'value' or 'value_getter' "
            f"at {rule_path}"
        )
        raise InvalidRuleError(msg)

    if has_value_getter:
        require_path_field(node, "value_getter", rule_path)


def _resolve_right_operand(
    node: dict[str, Any],
    context: dict[str, Any],
    rule_path: str,
) -> Any:
    if "value_getter" in node:
        value_path = require_path_field(node, "value_getter", rule_path)
        return resolve_path(context, value_path)
    return node["value"]


def resolve_compare(
    node: dict[str, Any],
    context: dict[str, Any],
    rule_path: str,
) -> bool:
    """Evaluate a compare node against the context."""
    _validate_compare_node(node, rule_path)

    op = node["op"]
    left_path = require_path_field(node, "path", rule_path)
    left = resolve_path(context, left_path)
    right = _resolve_right_operand(node, context, rule_path)
    return apply_operator(op, left, right)
