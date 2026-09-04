"""Weighted event selection (spec §6.3)."""

from __future__ import annotations

from couple_simulator_engine.conditions import (
    build_evaluation_context,
    evaluation_mode,
    should_apply,
)
from couple_simulator_engine.content.answers import AnswerBank
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.enums import PlayerRole
from couple_simulator_engine.session import GameSession
from couple_simulator_engine.snapshot import LoadedGame


def occurrences_in_session(session: GameSession, event_id: str) -> int:
    """Count how many times ``event_id`` appears in the session play history."""
    return session.events_played_ids.count(event_id)


def _matches_player_role(session: GameSession, event: EventDefinition) -> bool:
    if event.player_role is None:
        return True
    mode = evaluation_mode(session)
    if event.player_role == PlayerRole.PARTNER_B:
        return mode == "couple"
    return mode == "solo"


def _is_eligible(session: GameSession, event: EventDefinition) -> bool:
    if occurrences_in_session(session, event.id) >= event.max_occurrences:
        return False
    if event.life_stage is not None and event.life_stage != session.state.life_stage:
        return False
    if not _matches_player_role(session, event):
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


def _resolve_base_weight(session: GameSession, event: EventDefinition) -> float:
    """Return ``event.weight``, or the first matching ``weight_rules`` entry."""
    if not event.weight_rules:
        return event.weight
    ctx = build_evaluation_context(session, event, [])
    for rule in event.weight_rules:
        if should_apply(rule.when, ctx):
            return rule.weight
    return event.weight


def _selection_weight(
    session: GameSession,
    event: EventDefinition,
    *,
    bank: AnswerBank | None,
    boost: float,
) -> float:
    base = _resolve_base_weight(session, event)
    if bank is None or not event.use_answer_bank:
        return base
    if bank.partner_a_answers(event) is None:
        return base
    return base * boost


def _pick_weighted(
    session: GameSession,
    catalog: ContentCatalog,
    loaded: LoadedGame | None,
) -> EventDefinition | None:
    eligible = eligible_events(session, catalog)
    if not eligible:
        return None
    prefer_bank = loaded is not None and loaded.prefer_answer_bank_events
    bank = loaded.answer_bank if prefer_bank else None
    boost = session.config.answer_bank_preference_boost if prefer_bank else 1.0
    pairs = [
        (event, _selection_weight(session, event, bank=bank, boost=boost))
        for event in eligible
    ]
    return session.rng.weighted_choice(pairs)


def select_next_event(
    session: GameSession, catalog: ContentCatalog
) -> EventDefinition | None:
    """Return one eligible event by weight, or ``None`` if none remain."""
    return _pick_weighted(session, catalog, loaded=None)


def select_next_event_for_loaded(
    loaded: LoadedGame, catalog: ContentCatalog
) -> EventDefinition | None:
    """Weighted pick; boost covered events when ``prefer_answer_bank_events``."""
    return _pick_weighted(loaded.session, catalog, loaded)
