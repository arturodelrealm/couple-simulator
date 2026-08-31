"""Couple-level simulation state. Age and compatibility are derived from partners."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from couple_simulator_engine.clamp import clamp_stat
from couple_simulator_engine.enums import LifeStage, PlayerSex, RelationshipStatus
from couple_simulator_engine.player import Player

_DERIVED_STATS = frozenset({"age", "compatibility"})
_COUPLE_STATS = frozenset(
    {"finances", "adventures", "career", "quality_of_life", "children"}
)


def _default_partner_a() -> Player:
    return Player(id="partner_a", name="Partner A", sex=PlayerSex.OTHER)


def _default_partner_b() -> Player:
    return Player(id="partner_b", name="Partner B", sex=PlayerSex.OTHER)


@dataclass
class SimulationState:
    partner_a: Player = field(default_factory=_default_partner_a)
    partner_b: Player = field(default_factory=_default_partner_b)
    finances: int = 50
    adventures: int = 50
    career: int = 50
    quality_of_life: int = 50
    children: int = 0
    life_stage: LifeStage = LifeStage.YOUTH
    relationship_status: RelationshipStatus = RelationshipStatus.TOGETHER

    @property
    def age(self) -> int:
        """Couple narrative age: the younger partner's simulation age."""
        return min(self.partner_a.simulation_age, self.partner_b.simulation_age)

    @property
    def compatibility(self) -> int:
        """Couple compatibility: the lower of the two partners' simulation happiness."""
        return min(
            self.partner_a.simulation_relation_happiness,
            self.partner_b.simulation_relation_happiness,
        )

    def partners(self) -> tuple[Player, Player]:
        return (self.partner_a, self.partner_b)

    def begin_simulation(self) -> None:
        """Start a run from persisted game stats; does not overwrite game fields."""
        self.partner_a.begin_simulation()
        self.partner_b.begin_simulation()

    def to_dict(self) -> dict[str, Any]:
        """Dict for ``rules_evaluator`` context under the ``state/`` path prefix."""
        return {
            "age": self.age,
            "compatibility": self.compatibility,
            "finances": self.finances,
            "adventures": self.adventures,
            "career": self.career,
            "quality_of_life": self.quality_of_life,
            "children": self.children,
            "life_stage": self.life_stage.value,
            "relationship_status": self.relationship_status.value,
        }

    def set_stat(self, variable: str, value: int) -> int:
        """Assign a clamped couple-level stat (not derived age or compatibility)."""
        if variable in _DERIVED_STATS:
            raise ValueError(
                f"'{variable}' is derived from players; mutate simulation_age "
                "or simulation_relation_happiness on a Player"
            )
        if variable not in _COUPLE_STATS:
            raise ValueError(f"Unknown stat '{variable}'")
        clamped = clamp_stat(variable, value)
        setattr(self, variable, clamped)
        return clamped
