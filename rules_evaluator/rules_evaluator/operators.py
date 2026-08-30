"""Comparison operators for compare nodes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rules_evaluator.errors import UnknownOperatorError
from rules_evaluator.nodes import (
    OP_CONTAINS,
    OP_EQ,
    OP_GT,
    OP_GTE,
    OP_IN,
    OP_LT,
    OP_LTE,
    OP_NEQ,
    OPERATORS,
)


def apply_operator(op: str, left: Any, right: Any) -> bool:
    """Apply a comparison operator to left and right operands."""
    if op not in OPERATORS:
        msg = f"unsupported operator '{op}' in compare node"
        raise UnknownOperatorError(msg)

    if left is None:
        if op == OP_EQ:
            return right is None
        if op == OP_NEQ:
            return right is not None
        return False

    if op == OP_EQ:
        return left == right
    if op == OP_NEQ:
        return left != right
    if op == OP_IN:
        if not isinstance(right, Iterable) or isinstance(right, (str, bytes)):
            return False
        return left in right

    if op == OP_CONTAINS:
        if not isinstance(left, Iterable) or isinstance(left, (str, bytes)):
            return False
        return right in left

    try:
        if op == OP_GT:
            return left > right
        if op == OP_GTE:
            return left >= right
        if op == OP_LT:
            return left < right
        if op == OP_LTE:
            return left <= right
    except TypeError:
        return False

    return False
