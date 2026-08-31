"""Event selection filters and weighted pick (spec §6.3)."""

from unittest.mock import MagicMock

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OptionDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import LifeStage, PlayerSex
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.selection.event_selector import select_next_event
from couple_simulator_engine.session import GameSession
from couple_simulator_engine.state import SimulationState


def _session(
    *,
    finances: int = 50,
    age: int = 22,
    life_stage: LifeStage = LifeStage.YOUTH,
    events_played_ids: list[str] | None = None,
) -> GameSession:
    state = SimulationState()
    state.begin_simulation()
    state.set_stat("finances", finances)
    state.partner_a.set_simulation_age(age)
    state.partner_b.set_simulation_age(age)
    state.life_stage = life_stage
    return GameSession(
        session_id="s1",
        player=Player(id="p1", name="Alex", sex=PlayerSex.FEMALE),
        state=state,
        config=GameConfig(),
        rng=SeededRNG(1),
        events_played_ids=list(events_played_ids or []),
        events_played=len(events_played_ids or []),
    )


def _event(
    event_id: str,
    *,
    eligibility: dict[str, object] | None = None,
    life_stage: LifeStage | None = None,
    weight: float = 1.0,
    max_occurrences: int = 1,
) -> EventDefinition:
    return EventDefinition(
        id=event_id,
        title=event_id,
        description=None,
        tags=(),
        life_stage=life_stage,
        eligibility=eligibility,
        questions=(
            QuestionDefinition(
                id="q",
                text="Q",
                options=(OptionDefinition(id="a", text="A"),),
            ),
        ),
        outcomes=(),
        default_actions=(),
        mismatch_actions=(),
        weight=weight,
        max_occurrences=max_occurrences,
    )


_FINANCES_GTE_40: dict[str, object] = {
    "type": "compare",
    "path": "state/finances",
    "op": "gte",
    "value": 40,
}


def test_failing_eligibility_never_selected() -> None:
    poor = _event("needs_money", eligibility=_FINANCES_GTE_40)
    catalog = ContentCatalog([poor])
    session = _session(finances=20)
    assert select_next_event(session, catalog) is None


def test_max_occurrences_excludes_event() -> None:
    event = _event("once", max_occurrences=1)
    catalog = ContentCatalog([event])
    session = _session(events_played_ids=["once"])
    assert select_next_event(session, catalog) is None


def test_life_stage_mismatch_excluded() -> None:
    adult_only = _event("adult_only", life_stage=LifeStage.ADULT)
    catalog = ContentCatalog([adult_only])
    session = _session(life_stage=LifeStage.YOUTH)
    assert select_next_event(session, catalog) is None


def test_single_eligible_event_always_chosen() -> None:
    ineligible = _event("needs_money", eligibility=_FINANCES_GTE_40)
    eligible = _event("always")
    catalog = ContentCatalog([ineligible, eligible])
    session = _session(finances=20)
    chosen = select_next_event(session, catalog)
    assert chosen is not None
    assert chosen.id == "always"


def test_weighted_selection_favors_higher_weight() -> None:
    low = _event("low", weight=1.0)
    high = _event("high", weight=99.0)
    catalog = ContentCatalog([low, high])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = (
        lambda pairs: max(pairs, key=lambda item: item[1])[0]
    )
    session.rng = mock_rng
    chosen = select_next_event(session, catalog)
    assert chosen is high
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("low", 1.0),
        ("high", 99.0),
    }
