"""Session-level configuration for V0."""

from dataclasses import dataclass


@dataclass
class GameConfig:
    max_events: int = 5
    conflict_partner_b_weight: float = 0.65
    conflict_partner_a_weight: float = 0.35
    answer_bank_preference_boost: float = 2.0
    compatibility_mismatch_penalty: int = 10
    compatibility_match_bonus: int = 5
    conflict_winner_bonus: int = 2
    conflict_loser_penalty: int = 2
