"""Default GameConfig and engine enums."""

from couple_simulator_engine.config import DEFAULT_MAX_EVENTS, GameConfig
from couple_simulator_engine.enums import ConflictStrategy, PlayerRole


def test_game_config_defaults() -> None:
    config = GameConfig()
    assert config.max_events == DEFAULT_MAX_EVENTS
    assert DEFAULT_MAX_EVENTS == 15
    assert config.conflict_partner_b_weight == 0.65
    assert config.conflict_partner_a_weight == 0.35
    assert config.answer_bank_preference_boost == 2.0
    assert config.compatibility_mismatch_penalty == 10
    assert config.compatibility_match_bonus == 5
    assert config.conflict_winner_bonus == 2
    assert config.conflict_loser_penalty == 2
    assert config.passive_income_default == 2
    assert config.passive_income_by_band == {"low": 4, "mid": 6, "high": 8}
    assert config.passive_upkeep_children == 2
    assert config.passive_upkeep_excellent_housing == 1
    assert config.passive_income_enabled is True


def test_passive_income_defaults_match_spec() -> None:
    config = GameConfig()
    assert config.passive_income_default == 2
    assert config.passive_income_by_band == {"low": 4, "mid": 6, "high": 8}


def test_player_role_and_conflict_strategy() -> None:
    assert PlayerRole.PARTNER_A == "partner_a"
    assert PlayerRole.PARTNER_B == "partner_b"
    assert ConflictStrategy.WEIGHTED_PLAYER == "weighted_player"
