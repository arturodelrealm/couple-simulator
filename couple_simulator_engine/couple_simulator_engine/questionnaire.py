"""Partner A questionnaire catalog helpers (no session, no eligibility)."""

from __future__ import annotations

from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.enums import PlayerRole, PlayerSex
from couple_simulator_engine.session import EventPresentation


def list_partner_a_questionnaire_events(
    catalog: ContentCatalog,
) -> tuple[EventDefinition, ...]:
    """Return A-eligible events sorted by id, ignoring eligibility and life stage.

    Excludes only events whose ``player_role`` is Partner B.
    """
    events = [
        event
        for event in catalog.all_events()
        if event.player_role != PlayerRole.PARTNER_B
    ]
    events.sort(key=lambda event: event.id)
    return tuple(events)


def present_partner_a_questionnaire_events(
    engine: GameEngine,
    catalog: ContentCatalog,
    *,
    player_sex: PlayerSex,
) -> tuple[EventPresentation, ...]:
    """Present each questionnaire event for Partner A without mutating state."""
    return tuple(
        engine.present_event(
            event,
            player_role=PlayerRole.PARTNER_A,
            player_sex=player_sex,
        )
        for event in list_partner_a_questionnaire_events(catalog)
    )
