"""Event selection filters and weighted pick (spec §6.3)."""

from unittest.mock import MagicMock

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.answers import AnswerBank
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OptionDefinition,
    QuestionDefinition,
    WeightRuleDefinition,
)
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.enums import LifeStage, PlayerRole, PlayerSex
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.selection.event_selector import (
    select_next_event,
    select_next_event_for_loaded,
)
from couple_simulator_engine.session import GameSession, RecordedAnswer
from couple_simulator_engine.snapshot import (
    LoadedGame,
    PlayerRoleName,
    sequential_prefer_answer_bank_events,
)
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
    weight_rules: tuple[WeightRuleDefinition, ...] = (),
    max_occurrences: int = 1,
    player_role: PlayerRole | None = None,
    use_answer_bank: bool = True,
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
        weight_rules=weight_rules,
        max_occurrences=max_occurrences,
        player_role=player_role,
        use_answer_bank=use_answer_bank,
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
    mock_rng.weighted_choice.side_effect = lambda pairs: max(
        pairs, key=lambda item: item[1]
    )[0]
    session.rng = mock_rng
    chosen = select_next_event(session, catalog)
    assert chosen is high
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("low", 1.0),
        ("high", 99.0),
    }


_COMPAT_LT_20: dict[str, object] = {
    "type": "compare",
    "path": "state/compatibility",
    "op": "lt",
    "value": 20,
}


def _set_compatibility(session: GameSession, value: int) -> None:
    session.state.partner_a.set_simulation_relation_happiness(value)
    session.state.partner_b.set_simulation_relation_happiness(value)


def test_weight_rules_override_base_weight_when_condition_matches() -> None:
    event = _event(
        "conditional",
        weight=1.0,
        weight_rules=(WeightRuleDefinition(when=_COMPAT_LT_20, weight=2.0),),
    )
    catalog = ContentCatalog([event])
    session = _session()
    _set_compatibility(session, 15)
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    select_next_event(session, catalog)
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert pairs[0][1] == 2.0


def test_weight_rules_fall_back_to_base_weight_when_no_rule_matches() -> None:
    event = _event(
        "conditional",
        weight=1.0,
        weight_rules=(WeightRuleDefinition(when=_COMPAT_LT_20, weight=2.0),),
    )
    catalog = ContentCatalog([event])
    session = _session()
    _set_compatibility(session, 25)
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    select_next_event(session, catalog)
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert pairs[0][1] == 1.0


def test_weight_rules_use_first_matching_rule() -> None:
    event = _event(
        "conditional",
        weight=1.0,
        weight_rules=(
            WeightRuleDefinition(when=_COMPAT_LT_20, weight=2.0),
            WeightRuleDefinition(
                when={
                    "type": "compare",
                    "path": "state/compatibility",
                    "op": "lt",
                    "value": 40,
                },
                weight=5.0,
            ),
        ),
    )
    catalog = ContentCatalog([event])
    session = _session()
    _set_compatibility(session, 15)
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    select_next_event(session, catalog)
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert pairs[0][1] == 2.0


def _loaded(
    session: GameSession,
    *,
    player_role: PlayerRoleName,
    answers: list[RecordedAnswer] | None = None,
) -> LoadedGame:
    return LoadedGame(
        game_id="g1",
        mode="couple",
        session=session,
        answer_bank=AnswerBank.from_recorded_answers(answers or []),
        partner_a_runs=[],
        player_role=player_role,
        run_number=1,
        prefer_answer_bank_events=sequential_prefer_answer_bank_events(player_role),
    )


def test_loaded_partner_b_boosts_covered_event_weight() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_b",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    assert select_next_event_for_loaded(loaded, catalog) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 2.0),
    }


def test_prefer_answer_bank_events_boosts_regardless_of_player_role() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_a",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    loaded.prefer_answer_bank_events = True
    assert select_next_event_for_loaded(loaded, catalog) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 2.0),
    }


def test_cleared_prefer_flag_skips_boost_on_partner_b() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_b",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    loaded.prefer_answer_bank_events = False
    assert select_next_event_for_loaded(loaded, catalog) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 1.0),
    }


def test_loaded_partner_a_does_not_boost_covered_event_weight() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_a",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    assert select_next_event_for_loaded(loaded, catalog) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 1.0),
    }


def test_loaded_incomplete_coverage_keeps_unboosted_weight() -> None:
    two_q = EventDefinition(
        id="two_q",
        title="two_q",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Q1",
                options=(OptionDefinition(id="a", text="A"),),
            ),
            QuestionDefinition(
                id="q2",
                text="Q2",
                options=(OptionDefinition(id="b", text="B"),),
            ),
        ),
        outcomes=(),
        default_actions=(),
        mismatch_actions=(),
        weight=3.0,
        max_occurrences=1,
    )
    catalog = ContentCatalog([two_q])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_b",
        answers=[RecordedAnswer(event_id="two_q", question_id="q1", option_id="a")],
    )
    assert select_next_event_for_loaded(loaded, catalog) is two_q
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert pairs == [(two_q, 3.0)]


def test_loaded_empty_eligible_returns_none() -> None:
    adult_only = _event("adult_only", life_stage=LifeStage.ADULT)
    catalog = ContentCatalog([adult_only])
    loaded = _loaded(_session(life_stage=LifeStage.YOUTH), player_role="partner_b")
    assert select_next_event_for_loaded(loaded, catalog) is None


def test_engine_select_next_event_session_stays_unboosted() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    engine = GameEngine(catalog)
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    assert engine.select_next_event(session) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 1.0),
    }


def test_engine_select_next_event_loaded_partner_b_boosts() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0)
    catalog = ContentCatalog([uncovered, covered])
    engine = GameEngine(catalog)
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_b",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    assert engine.select_next_event(loaded) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 2.0),
    }


def test_partner_b_only_event_excluded_from_partner_a_session() -> None:
    event = _event("b_only", player_role=PlayerRole.PARTNER_B)
    catalog = ContentCatalog([event])
    session = _session()
    assert select_next_event(session, catalog) is None
    session.player = session.state.partner_b
    chosen = select_next_event(session, catalog)
    assert chosen is event


def test_use_answer_bank_false_skips_coverage_boost() -> None:
    uncovered = _event("uncovered", weight=1.0)
    covered = _event("covered", weight=1.0, use_answer_bank=False)
    catalog = ContentCatalog([uncovered, covered])
    session = _session()
    mock_rng = MagicMock()
    mock_rng.weighted_choice.side_effect = lambda pairs: pairs[0][0]
    session.rng = mock_rng
    loaded = _loaded(
        session,
        player_role="partner_b",
        answers=[
            RecordedAnswer(event_id="covered", question_id="q", option_id="a"),
        ],
    )
    assert select_next_event_for_loaded(loaded, catalog) is not None
    pairs = mock_rng.weighted_choice.call_args[0][0]
    assert {(event.id, weight) for event, weight in pairs} == {
        ("uncovered", 1.0),
        ("covered", 1.0),
    }
