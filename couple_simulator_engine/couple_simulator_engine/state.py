"""Couple-level simulation state. Age and compatibility are derived from partners."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from couple_simulator_engine.clamp import clamp_stat
from couple_simulator_engine.enums import (
    HousingQuality,
    HousingType,
    LifeStage,
    PlayerSex,
    RelationshipStatus,
)
from couple_simulator_engine.player import Player

_DERIVED_STATS = frozenset({"age", "compatibility"})
_COUPLE_STATS = frozenset(
    {"finances", "quality_of_life", "children", "wellness", "mismatches"}
)
_DEFAULT_HOUSING_PLACE = "Providencia"


@dataclass
class Housing:
    place: str = _DEFAULT_HOUSING_PLACE
    type: HousingType = HousingType.APARTMENT
    quality: HousingQuality = HousingQuality.OK


@dataclass
class Mascot:
    species: str
    name: str


def _default_partner_a() -> Player:
    return Player(id="partner_a", name="Partner A", sex=PlayerSex.OTHER)


def _default_partner_b() -> Player:
    return Player(id="partner_b", name="Partner B", sex=PlayerSex.OTHER)


@dataclass
class SimulationState:
    partner_a: Player = field(default_factory=_default_partner_a)
    partner_b: Player = field(default_factory=_default_partner_b)
    finances: int = 15
    quality_of_life: int = 20
    children: int = 0
    wellness: int = 50
    mismatches: int = 0
    matches: int = 0
    compared_questions: int = 0
    housing: Housing = field(default_factory=Housing)
    mascot: Mascot | None = None
    tags: dict[str, Any] = field(default_factory=dict)
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
            "quality_of_life": self.quality_of_life,
            "children": self.children,
            "wellness": self.wellness,
            "mismatches": self.mismatches,
            "matches": self.matches,
            "compared_questions": self.compared_questions,
            "housing": {
                "place": self.housing.place,
                "type": self.housing.type.value,
                "quality": self.housing.quality.value,
            },
            "mascot": (
                None
                if self.mascot is None
                else {"species": self.mascot.species, "name": self.mascot.name}
            ),
            "tags": dict(self.tags),
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
