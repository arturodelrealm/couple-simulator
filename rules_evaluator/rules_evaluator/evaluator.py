"""Recursive evaluation of condition expression trees."""

from __future__ import annotations

from typing import Any

from rules_evaluator.errors import InvalidRuleError
from rules_evaluator.nodes import (
    MAX_ITEMS_PER_NODE,
    MAX_TREE_DEPTH,
    NODE_TYPES,
    TYPE_ALL,
    TYPE_COMPARE,
    TYPE_NOT,
)
from rules_evaluator.resolver import resolve_compare


def evaluate_node(
    node: dict[str, Any],
    context: dict[str, Any],
    *,
    path: str = "root",
    depth: int = 0,
) -> bool:
    """Evaluate a normalized condition node against the context."""
    if depth > MAX_TREE_DEPTH:
        msg = f"rule tree exceeds maximum depth of {MAX_TREE_DEPTH} at {path}"
        raise InvalidRuleError(msg)

    node_type = node.get("type")
    if node_type not in NODE_TYPES:
        label = node_type if node_type is not None else "<missing>"
        msg = f"unknown node type '{label}' at {path}"
        raise InvalidRuleError(msg)

    if node_type == TYPE_COMPARE:
        return resolve_compare(node, context, path)

    items = node.get("items")
    if not isinstance(items, list):
        msg = f"'items' must be a list in '{node_type}' node at {path}"
        raise InvalidRuleError(msg)

    if len(items) > MAX_ITEMS_PER_NODE:
        msg = (
            f"'items' exceeds maximum size of {MAX_ITEMS_PER_NODE} "
            f"in '{node_type}' node at {path}"
        )
        raise InvalidRuleError(msg)

    if node_type == TYPE_NOT:
        if len(items) != 1:
            msg = f"'not' node must have exactly one child at {path}"
            raise InvalidRuleError(msg)
        child = items[0]
        if not isinstance(child, dict):
            msg = f"child of 'not' node must be a dict at {path}"
            raise InvalidRuleError(msg)
        return not evaluate_node(
            child,
            context,
            path=f"{path}.items[0]",
            depth=depth + 1,
        )

    results: list[bool] = []
    for index, child in enumerate(items):
        if not isinstance(child, dict):
            msg = f"child at {path}.items[{index}] must be a dict"
            raise InvalidRuleError(msg)
        results.append(
            evaluate_node(
                child,
                context,
                path=f"{path}.items[{index}]",
                depth=depth + 1,
            )
        )

    if node_type == TYPE_ALL:
        return all(results)
    return any(results)
