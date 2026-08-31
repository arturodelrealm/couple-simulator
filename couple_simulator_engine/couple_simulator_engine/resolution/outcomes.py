"""Outcome matching for event resolution (spec §6.4, decision P2)."""

from __future__ import annotations

from typing import Any

from couple_simulator_engine.conditions import should_apply
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OutcomeDefinition,
)


def matching_outcomes(
    event: EventDefinition,
    ctx: dict[str, Any],
) -> list[OutcomeDefinition]:
    """Return every outcome whose ``when`` matches, in definition order.

    Several outcomes may apply in one event (P2); this is not first-wins.
    """
    return [outcome for outcome in event.outcomes if should_apply(outcome.when, ctx)]
