"""Default GameConfig and engine enums."""

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import ConflictStrategy, PlayerRole


def test_game_config_defaults() -> None:
    config = GameConfig()
    assert config.max_events == 5
    assert config.conflict_partner_b_weight == 0.65
    assert config.conflict_partner_a_weight == 0.35
    assert config.answer_bank_preference_boost == 2.0
    assert config.compatibility_mismatch_penalty == 10
    assert config.compatibility_match_bonus == 5
    assert config.conflict_winner_bonus == 2
    assert config.conflict_loser_penalty == 2


def test_player_role_and_conflict_strategy() -> None:
    assert PlayerRole.PARTNER_A == "partner_a"
    assert PlayerRole.PARTNER_B == "partner_b"
    assert ConflictStrategy.WEIGHTED_PLAYER == "weighted_player"