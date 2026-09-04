"""Reproducibility tests for SeededRNG and GameConfig defaults."""

from couple_simulator_engine.config import DEFAULT_MAX_EVENTS, GameConfig
from couple_simulator_engine.rng import SeededRNG


def test_game_config_default_max_events() -> None:
    assert GameConfig().max_events == DEFAULT_MAX_EVENTS
    assert DEFAULT_MAX_EVENTS == 15


def test_omitted_seed_is_stored_as_int() -> None:
    rng = SeededRNG(None)
    assert isinstance(rng.seed, int)
    assert rng.seed >= 0
    reconstructed = SeededRNG(rng.seed)
    assert reconstructed.seed == rng.seed


def test_explicit_seed_is_unchanged() -> None:
    assert SeededRNG(42).seed == 42


def test_weighted_choice_reproducible() -> None:
    pairs = [("a", 1.0), ("b", 2.0), ("c", 3.0)]
    first = SeededRNG(42)
    second = SeededRNG(42)
    samples_first = [first.weighted_choice(pairs) for _ in range(30)]
    samples_second = [second.weighted_choice(pairs) for _ in range(30)]
    assert samples_first == samples_second


def test_normal_reproducible() -> None:
    first = SeededRNG(7)
    second = SeededRNG(7)
    samples_first = [first.normal(10, 2) for _ in range(20)]
    samples_second = [second.normal(10, 2) for _ in range(20)]
    assert samples_first == samples_second
