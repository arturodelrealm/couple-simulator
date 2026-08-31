"""Resolve content numeric args (fixed values and V0 distributions)."""

from __future__ import annotations

from typing import Any

from couple_simulator_engine.rng import SeededRNG


def resolve_value(value: Any, rng: SeededRNG) -> Any:
    """Resolve a content arg to a concrete value (spec §8.8).

    Plain numbers are returned as-is. Dicts with ``kind: fixed`` unwrap
    ``value``. Nested ``distribution`` specs are sampled via ``rng``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, dict):
        return value

    if "distribution" in value:
        return _sample_distribution(value["distribution"], rng)

    kind = value.get("kind")
    if kind == "fixed":
        return value["value"]
    if kind is not None:
        raise ValueError(f"Unknown value kind '{kind}'")
    return value


def _sample_distribution(spec: Any, rng: SeededRNG) -> int:
    if not isinstance(spec, dict):
        raise ValueError(f"Invalid distribution spec: {spec!r}")
    kind = spec.get("kind")
    params = spec.get("params") or {}
    if kind == "normal":
        return rng.normal(params["median"], params["std"])
    if kind == "uniform":
        return rng.uniform_int(int(params["min"]), int(params["max"]))
    raise ValueError(f"Unknown distribution kind '{kind}'")
