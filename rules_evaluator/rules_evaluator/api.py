"""Public API for evaluating condition expressions."""

from __future__ import annotations

from typing import Any

from rules_evaluator.evaluator import evaluate_node
from rules_evaluator.normalize import normalize_rule


def evaluate(rule: dict[str, Any] | list[Any] | None, context: dict[str, Any]) -> bool:
    """
    Evaluate a rule against a context dict.

    None, an empty dict, an empty list, or an empty ``all`` node evaluates to True.

    Compare nodes use ``path`` (and optionally ``value_getter``) to read from context.
    """
    if not isinstance(context, dict):
        msg = f"context must be a dict, got {type(context).__name__}"
        raise TypeError(msg)

    normalized = normalize_rule(rule)
    if normalized is None:
        return True

    return evaluate_node(normalized, context)


def evaluate_all(
    rules: list[dict[str, Any] | list[Any] | None],
    context: dict[str, Any],
) -> bool:
    """Evaluate every rule; return True only when all rules pass (implicit AND)."""
    if not rules:
        return True
    return all(evaluate(rule, context) for rule in rules)
