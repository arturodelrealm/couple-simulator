"""Session-level configuration for V0."""

from dataclasses import dataclass, field

DEFAULT_MAX_EVENTS = 15


def _default_passive_income_by_band() -> dict[str, int]:
    return {"low": 4, "mid": 6, "high": 8}


@dataclass
class GameConfig:
    max_events: int = DEFAULT_MAX_EVENTS
    conflict_partner_b_weight: float = 0.65
    conflict_partner_a_weight: float = 0.35
    answer_bank_preference_boost: float = 2.0
    compatibility_mismatch_penalty: int = 10
    compatibility_match_bonus: int = 5
    conflict_winner_bonus: int = 2
    conflict_loser_penalty: int = 2
    passive_income_default: int = 2
    passive_income_by_band: dict[str, int] = field(
        default_factory=_default_passive_income_by_band
    )
    passive_upkeep_children: int = 2
    passive_upkeep_excellent_housing: int = 1
    passive_income_enabled: bool = True
