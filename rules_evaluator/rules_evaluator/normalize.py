"""Rule normalization: flat lists, empty rules, and nested trees."""

from __future__ import annotations

from typing import Any

from rules_evaluator.errors import InvalidRuleError
from rules_evaluator.nodes import TYPE_ALL


def normalize_rule(rule: dict[str, Any] | list[Any] | None) -> dict[str, Any] | None:
    """
    Normalize a rule into a canonical tree node, or None when the rule is empty.

    - None → None
    - [] or {"type": "all", "items": []} → None
    - list → {"type": "all", "items": [...]}
    """
    if rule is None:
        return None

    if isinstance(rule, list):
        items = [normalize_rule(item) for item in rule]
        items = [item for item in items if item is not None]
        if not items:
            return None
        if len(items) == 1:
            return items[0]
        return {"type": TYPE_ALL, "items": items}

    if not isinstance(rule, dict):
        msg = f"rule must be a dict, list, or None, got {type(rule).__name__}"
        raise InvalidRuleError(msg)

    if not rule:
        return None

    if "type" not in rule:
        raise InvalidRuleError("missing 'type' field in rule node")

    node_type = rule["type"]
    if node_type == TYPE_ALL:
        items = rule.get("items", [])
        if not isinstance(items, list):
            raise InvalidRuleError("'items' must be a list in 'all' node")
        normalized_items = [normalize_rule(item) for item in items]
        normalized_items = [item for item in normalized_items if item is not None]
        if not normalized_items:
            return None
        if len(normalized_items) == 1:
            return normalized_items[0]
        return {"type": TYPE_ALL, "items": normalized_items}

    return dict(rule)
