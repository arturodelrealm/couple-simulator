"""Players in a couple: persisted game stats vs per-run simulation stats."""

from __future__ import annotations

from dataclasses import dataclass

from couple_simulator_engine.clamp import clamp_stat
from couple_simulator_engine.enums import PlayerSex

DEFAULT_GAME_AGE = 22
DEFAULT_RELATION_HAPPINESS = 100


@dataclass
class Player:
    """One partner with persisted game stats and per-run simulation stats."""

    id: str
    name: str
    sex: PlayerSex
    game_age: int = DEFAULT_GAME_AGE
    game_relation_happiness: int = DEFAULT_RELATION_HAPPINESS
    simulation_age: int = DEFAULT_GAME_AGE
    simulation_relation_happiness: int = DEFAULT_RELATION_HAPPINESS
    avatar_config: dict[str, str] | None = None

    def begin_simulation(self) -> None:
        """Copy game stats into this run without changing persisted game fields."""
        self.simulation_age = self.game_age
        self.simulation_relation_happiness = self.game_relation_happiness

    def set_simulation_age(self, value: int) -> int:
        self.simulation_age = clamp_stat("age", value)
        return self.simulation_age

    def set_simulation_relation_happiness(self, value: int) -> int:
        self.simulation_relation_happiness = clamp_stat("compatibility", value)
        return self.simulation_relation_happiness

    def set_game_age(self, value: int) -> int:
        self.game_age = clamp_stat("age", value)
        return self.game_age

    def set_game_relation_happiness(self, value: int) -> int:
        self.game_relation_happiness = clamp_stat("compatibility", value)
        return self.game_relation_happiness
