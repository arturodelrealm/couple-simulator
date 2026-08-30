"""Stat clamp rules for V0 (player and couple stats)."""

AGE_MIN = 18
CHILDREN_MIN = 0
STAT_MIN = 0
STAT_MAX = 100

_STAT_BOUNDS: dict[str, tuple[int | None, int | None]] = {
    "age": (AGE_MIN, None),
    "children": (CHILDREN_MIN, None),
    "compatibility": (STAT_MIN, STAT_MAX),
    "finances": (STAT_MIN, STAT_MAX),
    "adventures": (STAT_MIN, STAT_MAX),
    "career": (STAT_MIN, STAT_MAX),
    "quality_of_life": (STAT_MIN, STAT_MAX),
}


def clamp_stat(variable: str, value: int) -> int:
    """Clamp a stat value: 0–100 for bounded stats; min-only for age and children."""
    bounds = _STAT_BOUNDS.get(variable)
    if bounds is None:
        raise ValueError(f"Unknown stat '{variable}'")
    low, high = bounds
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value
