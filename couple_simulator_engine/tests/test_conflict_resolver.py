"""WEIGHTED_PLAYER ConflictResolver (65% B / 35% A)."""

from unittest.mock import MagicMock

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import ConflictStrategy
from couple_simulator_engine.resolution.conflict import ConflictResolver
from couple_simulator_engine.rng import SeededRNG


def test_equal_options_return_that_option_without_rolling() -> None:
    rng = SeededRNG(1)
    control = SeededRNG(1)
    winner = ConflictResolver().resolve("opt_same", "opt_same", rng, GameConfig())
    assert winner == "opt_same"
    assert rng.random() == control.random()


def test_differing_options_return_only_a_or_b() -> None:
    rng = SeededRNG(42)
    config = GameConfig()
    resolver = ConflictResolver()
    for _ in range(50):
        winner = resolver.resolve("opt_a", "opt_b", rng, config)
        assert winner in ("opt_a", "opt_b")


def test_fixed_seed_is_deterministic_and_both_partners_can_win() -> None:
    config = GameConfig()
    resolver = ConflictResolver()
    stream_a = SeededRNG(42)
    stream_b = SeededRNG(42)
    samples_a = [
        resolver.resolve("opt_a", "opt_b", stream_a, config) for _ in range(80)
    ]
    samples_b = [
        resolver.resolve("opt_a", "opt_b", stream_b, config) for _ in range(80)
    ]
    assert samples_a == samples_b
    assert "opt_a" in samples_a
    assert "opt_b" in samples_a


def test_weights_come_from_game_config_defaults() -> None:
    config = GameConfig()
    assert config.conflict_partner_b_weight == 0.65
    assert config.conflict_partner_a_weight == 0.35
    rng = MagicMock()
    rng.weighted_choice.return_value = "opt_b"
    winner = ConflictResolver().resolve("opt_a", "opt_b", rng, config)
    assert winner == "opt_b"
    pairs = rng.weighted_choice.call_args[0][0]
    assert pairs == (
        ("opt_b", 0.65),
        ("opt_a", 0.35),
    )


def test_strategy_is_weighted_player() -> None:
    assert ConflictResolver.strategy is ConflictStrategy.WEIGHTED_PLAYER
