"""Smoke tests for the couple_simulator_engine package scaffold."""

import couple_simulator_engine


def test_package_importable() -> None:
    assert couple_simulator_engine.__all__ == [
        "GameConfig",
        "GameEngine",
        "Player",
        "SeededRNG",
        "SimulationState",
    ]
    assert couple_simulator_engine.GameConfig().max_events == 5
