"""Tests for ``resolve_value`` (spec §8.8)."""

import pytest

from couple_simulator_engine.actions.distributions import resolve_value
from couple_simulator_engine.rng import SeededRNG


def test_plain_int_returned_as_is_without_consuming_rng() -> None:
    rng = SeededRNG(42)
    assert resolve_value(10, rng) == 10
    assert rng.normal(10, 2) == SeededRNG(42).normal(10, 2)


def test_plain_float_returned_as_is() -> None:
    assert resolve_value(1.5, SeededRNG(1)) == 1.5


def test_fixed_kind_unwraps_value() -> None:
    assert resolve_value({"kind": "fixed", "value": 7}, SeededRNG(1)) == 7


def test_normal_distribution_is_reproducible() -> None:
    spec = {
        "distribution": {"kind": "normal", "params": {"median": 10, "std": 2}}
    }
    first_rng = SeededRNG(7)
    second_rng = SeededRNG(7)
    first = [resolve_value(spec, first_rng) for _ in range(20)]
    second = [resolve_value(spec, second_rng) for _ in range(20)]
    assert first == second
    assert all(isinstance(sample, int) for sample in first)


def test_uniform_respects_min_max_inclusive() -> None:
    spec = {
        "distribution": {"kind": "uniform", "params": {"min": 1, "max": 3}}
    }
    rng = SeededRNG(99)
    samples = [resolve_value(spec, rng) for _ in range(80)]
    assert all(1 <= sample <= 3 for sample in samples)
    assert set(samples) == {1, 2, 3}


def test_unknown_distribution_kind_raises() -> None:
    spec = {"distribution": {"kind": "weighted_pick", "params": {}}}
    with pytest.raises(ValueError, match="Unknown distribution kind"):
        resolve_value(spec, SeededRNG(1))


def test_unknown_value_kind_raises() -> None:
    with pytest.raises(ValueError, match="Unknown value kind"):
        resolve_value({"kind": "one_of", "value": 1}, SeededRNG(1))
