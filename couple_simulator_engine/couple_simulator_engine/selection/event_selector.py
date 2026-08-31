"""Weighted event selection (spec §6.3)."""

from __future__ import annotations

from couple_simulator_engine.conditions import build_evaluation_context, should_apply
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.session import GameSession


def occurrences_in_session(session: GameSession, event_id: str) -> int:
    """Count how many times ``event_id`` appears in the session play history."""
    return session.events_played_ids.count(event_id)


def _is_eligible(session: GameSession, event: EventDefinition) -> bool:
    if occurrences_in_session(session, event.id) >= event.max_occurrences:
        return False
    if event.life_stage is not None and event.life_stage != session.state.life_stage:
        return False
    ctx = build_evaluation_context(session, event, [])
    return should_apply(event.eligibility, ctx)


def eligible_events(
    session: GameSession, catalog: ContentCatalog
) -> tuple[EventDefinition, ...]:
    """Events that pass eligibility, occurrence, and life-stage filters."""
    return tuple(
        event for event in catalog.all_events() if _is_eligible(session, event)
    )


def select_next_event(
    session: GameSession, catalog: ContentCatalog
) -> EventDefinition | None:
    """Return one eligible event by weight, or ``None`` if none remain."""
    eligible = eligible_events(session, catalog)
    if not eligible:
        return None
    pairs = [(event, event.weight) for event in eligible]
    return session.rng.weighted_choice(pairs)
