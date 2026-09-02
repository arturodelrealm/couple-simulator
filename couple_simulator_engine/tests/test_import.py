"""Smoke tests for the couple_simulator_engine package scaffold."""

import couple_simulator_engine


def test_package_importable() -> None:
    assert couple_simulator_engine.__all__ == [
        "AnswerBank",
        "ConflictStrategy",
        "GameConfig",
        "GameEngine",
        "GameSnapshot",
        "LoadedGame",
        "Player",
        "PlayerRole",
        "SeededRNG",
        "SimulationState",
    ]
    assert (
        couple_simulator_engine.PlayerRole.PARTNER_B.value == "partner_b"
    )
    assert (
        couple_simulator_engine.ConflictStrategy.WEIGHTED_PLAYER.value
        == "weighted_player"
    )
    config = couple_simulator_engine.GameConfig()
    assert config.max_events == 5
    assert config.conflict_partner_b_weight == 0.65
    assert config.conflict_partner_a_weight == 0.35
    assert config.answer_bank_preference_boost == 2.0
    assert config.compatibility_mismatch_penalty == 10
    assert config.compatibility_match_bonus == 5
    assert config.conflict_winner_bonus == 2
    assert config.conflict_loser_penalty == 2
