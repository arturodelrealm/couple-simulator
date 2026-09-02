"""Pick one option when partners disagree (V1: WEIGHTED_PLAYER)."""

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import ConflictStrategy
from couple_simulator_engine.rng import SeededRNG


class ConflictResolver:
    """Return exactly one option id per question; does not mutate simulation state."""

    strategy = ConflictStrategy.WEIGHTED_PLAYER

    def resolve(
        self,
        partner_a_option_id: str,
        partner_b_option_id: str,
        rng: SeededRNG,
        config: GameConfig,
    ) -> str:
        if partner_a_option_id == partner_b_option_id:
            return partner_a_option_id
        return rng.weighted_choice(
            (
                (partner_b_option_id, config.conflict_partner_b_weight),
                (partner_a_option_id, config.conflict_partner_a_weight),
            )
        )
