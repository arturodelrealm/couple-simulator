"""Path-based value resolution against evaluation contexts."""

from __future__ import annotations

from typing import Any

from rules_evaluator.errors import InvalidRuleError


def resolve_path(context: dict[str, Any], path: str) -> Any:
    """
    Resolve a slash-separated path against a nested context dict.

    Examples: ``state/finances``, ``flags/mismatch_on_question/destination``.

    Missing segments return ``None``. Lists support numeric index segments.
    """
    segments = parse_path(path)
    current: Any = context
    for segment in segments:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(segment)
            continue
        if isinstance(current, list):
            try:
                index = int(segment)
            except ValueError:
                return None
            if index < 0 or index >= len(current):
                return None
            current = current[index]
            continue
        return None
    return current


def parse_path(path: str) -> list[str]:
    if not isinstance(path, str) or not path.strip():
        msg = "path must be a non-empty string"
        raise InvalidRuleError(msg)

    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        msg = "path must contain at least one segment"
        raise InvalidRuleError(msg)
    return segments


def require_path_field(node: dict[str, Any], field: str, rule_path: str) -> str:
    if field not in node:
        msg = f"missing '{field}' in compare node at {rule_path}"
        raise InvalidRuleError(msg)

    path = node[field]
    if not isinstance(path, str):
        msg = f"'{field}' must be a string in compare node at {rule_path}"
        raise InvalidRuleError(msg)

    parse_path(path)
    return path
