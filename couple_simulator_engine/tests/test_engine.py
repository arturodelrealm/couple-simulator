"""GameEngine new_session hydrate and snapshot load/export."""

from unittest.mock import MagicMock

import pytest

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import (
    ContentCatalog,
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.session import Answer, RecordedAnswer
from couple_simulator_engine.snapshot import GameSnapshot, LoadedGame, RunSnapshot
from couple_simulator_engine.state import SimulationState


def _engine() -> GameEngine:
    return GameEngine(load_catalog(package_events_directory()))


def _named_player() -> Player:
    return Player(
        id="p-a",
        name="Jordan",
        sex=PlayerSex.MALE,
        game_age=30,
        game_relation_happiness=75,
    )


def test_new_session_places_player_on_partner_a_and_begins_simulation() -> None:
    engine = _engine()
    player = _named_player()
    session = engine.new_session(player, seed=42)
    assert session.player is player
    assert session.state.partner_a is player
    assert session.state.partner_a.name == "Jordan"
    assert session.state.partner_a.simulation_age == player.game_age
    assert session.state.partner_a.simulation_relation_happiness == 75
    assert session.state.partner_b.id == "partner_b"
    assert session.state.partner_b.name == "Partner B"
    assert session.state.partner_b.simulation_age == session.state.partner_b.game_age
    assert isinstance(session.rng.seed, int)
    assert session.rng.seed == 42
    assert session.config.max_events == 5


def test_new_session_omitted_partner_b_uses_default() -> None:
    session = _engine().new_session(_named_player())
    assert session.player is session.state.partner_a
    assert session.state.partner_b.id == "partner_b"
    assert session.state.partner_b.name == "Partner B"


def test_new_session_partner_b_role_sets_active_player_and_both_characters() -> None:
    partner_a = _named_player()
    partner_b = Player(
        id="p-b",
        name="Riley",
        sex=PlayerSex.FEMALE,
        game_age=28,
        game_relation_happiness=80,
    )
    session = _engine().new_session(
        partner_a, partner_b=partner_b, player_role="partner_b"
    )
    assert session.player is partner_b
    assert session.state.partner_a is partner_a
    assert session.state.partner_b is partner_b
    assert session.state.partner_b.simulation_age == 28
    assert session.state.partner_b.simulation_relation_happiness == 80
    assert session.state.partner_a.simulation_age == partner_a.game_age


def test_new_session_optional_max_events_overrides_config() -> None:
    engine = GameEngine(
        load_catalog(package_events_directory()), GameConfig(max_events=5)
    )
    session = engine.new_session(_named_player(), max_events=3)
    assert session.config.max_events == 3


def test_load_game_export_snapshot_round_trip() -> None:
    engine = _engine()
    player = _named_player()
    player.begin_simulation()
    player.set_simulation_age(31)
    state = SimulationState(partner_a=player)
    snapshot = GameSnapshot(
        game_id="g1",
        mode="solo",
        active_run=RunSnapshot(
            run_id="r1",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=99,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=[
                RecordedAnswer(
                    event_id="weekend_trip",
                    question_id="weekend_plan",
                    option_id="stay_home",
                )
            ],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
            state=state,
        ),
        partner_a_runs=[],
        config=GameConfig(max_events=5),
    )
    loaded = engine.load_game(snapshot)
    assert loaded.session.rng.seed == 99
    assert loaded.session.state.partner_a.name == "Jordan"
    weekend = engine.catalog.get("weekend_trip")
    assert weekend is not None
    assert loaded.answer_bank.has_coverage_for(weekend) is True
    exported = engine.export_snapshot(loaded)
    assert exported.game_id == "g1"
    assert exported.active_run.rng_seed == 99
    assert exported.active_run.answers[0].option_id == "stay_home"
    assert exported.active_run.state.partner_a.simulation_age == 31


def test_load_then_select_present_export_keeps_current_event_id() -> None:
    engine = _engine()
    session = engine.new_session(_named_player(), seed=42)
    snapshot = engine.export_snapshot(
        engine.load_game(
            GameSnapshot(
                game_id="g2",
                mode="solo",
                active_run=RunSnapshot(
                    run_id=session.session_id,
                    player_role="partner_a",
                    run_number=1,
                    status=session.status,
                    rng_seed=session.rng.seed,
                    events_played=session.events_played,
                    events_played_ids=list(session.events_played_ids),
                    timeline=list(session.timeline),
                    answers=list(session.answers),
                    event_variables=dict(session.event_variables),
                    current_event_id=None,
                    end_reason=None,
                    max_events=session.config.max_events,
                    state=session.state,
                ),
                partner_a_runs=[],
                config=session.config,
            )
        )
    )
    loaded = engine.load_game(snapshot)
    event = engine.select_next_event(loaded.session)
    assert event is not None
    engine.present_event(event)
    loaded.session.current_event_id = event.id
    exported = engine.export_snapshot(loaded)
    assert exported.active_run.current_event_id == event.id


def test_load_game_rejects_invalid_player_role() -> None:
    engine = _engine()
    snapshot = GameSnapshot(
        game_id="g3",
        mode="solo",
        active_run=RunSnapshot(
            run_id="r-bad",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=1,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=[],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
        ),
        partner_a_runs=[],
        config=GameConfig(),
    )
    snapshot.active_run.player_role = "spectator"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="player_role"):
        engine.load_game(snapshot)


def _two_question_event() -> EventDefinition:
    return EventDefinition(
        id="weekend_trip",
        title="Weekend trip",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="go",
                text="Go?",
                options=(
                    OptionDefinition(id="yes", text="Yes"),
                    OptionDefinition(id="no", text="No"),
                ),
            ),
            QuestionDefinition(
                id="where",
                text="Where?",
                options=(
                    OptionDefinition(id="beach", text="Beach"),
                    OptionDefinition(id="city", text="City"),
                ),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )


def _loaded_with_answers(answers: list[RecordedAnswer]) -> LoadedGame:
    player = _named_player()
    player.begin_simulation()
    snapshot = GameSnapshot(
        game_id="g-bank",
        mode="solo",
        active_run=RunSnapshot(
            run_id="r-bank",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=1,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=answers,
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
            state=SimulationState(partner_a=player),
        ),
        partner_a_runs=[],
        config=GameConfig(),
    )
    return _engine().load_game(snapshot)


def test_partner_a_answers_returns_none_when_any_question_missing() -> None:
    loaded = _loaded_with_answers(
        [RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes")]
    )
    assert _engine().partner_a_answers(loaded, _two_question_event()) is None


def test_partner_a_answers_returns_one_answer_per_question_when_complete() -> None:
    loaded = _loaded_with_answers(
        [
            RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes"),
            RecordedAnswer(
                event_id="weekend_trip", question_id="where", option_id="beach"
            ),
        ]
    )
    resolved = _engine().partner_a_answers(loaded, _two_question_event())
    assert resolved is not None
    assert [(item.question_id, item.option_id) for item in resolved] == [
        ("go", "yes"),
        ("where", "beach"),
    ]


def _duo_choice_event() -> EventDefinition:
    return EventDefinition(
        id="duo_choice",
        title="Duo",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Choose",
                options=(
                    OptionDefinition(
                        id="opt_a",
                        text="A",
                        actions=(
                            ActionDefinition(
                                type="modify_stat",
                                args={"variable": "finances", "delta": 1},
                            ),
                        ),
                    ),
                    OptionDefinition(
                        id="opt_b",
                        text="B",
                        actions=(
                            ActionDefinition(
                                type="modify_stat",
                                args={"variable": "finances", "delta": 20},
                            ),
                        ),
                    ),
                ),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )


def _duo_state(*, happiness: int = 70) -> SimulationState:
    partner_a = Player(
        id="p-a",
        name="Jordan",
        sex=PlayerSex.MALE,
        game_age=30,
        game_relation_happiness=happiness,
    )
    partner_b = Player(
        id="p-b",
        name="Riley",
        sex=PlayerSex.FEMALE,
        game_age=28,
        game_relation_happiness=happiness,
    )
    state = SimulationState(partner_a=partner_a, partner_b=partner_b)
    state.begin_simulation()
    return state


def _partner_a_run(answers: list[RecordedAnswer]) -> RunSnapshot:
    return RunSnapshot(
        run_id="run-a",
        player_role="partner_a",
        run_number=1,
        status=SessionStatus.FINISHED,
        rng_seed=1,
        events_played=1,
        events_played_ids=["duo_choice"],
        timeline=[],
        answers=answers,
        event_variables={},
        current_event_id=None,
        end_reason="max_events",
        max_events=5,
        state=_duo_state(),
    )


def _partner_b_snapshot(
    partner_a_runs: list[RunSnapshot], *, rng_seed: int = 7
) -> GameSnapshot:
    return GameSnapshot(
        game_id="g-duo",
        mode="couple",
        active_run=RunSnapshot(
            run_id="run-b",
            player_role="partner_b",
            run_number=2,
            status=SessionStatus.ACTIVE,
            rng_seed=rng_seed,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=[],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
            state=_duo_state(),
        ),
        partner_a_runs=partner_a_runs,
        config=GameConfig(),
    )


def _duo_engine(event: EventDefinition) -> GameEngine:
    return GameEngine(ContentCatalog([event]))


def test_loaded_partner_b_submit_match_applies_bonus_not_personal() -> None:
    event = _duo_choice_event()
    engine = _duo_engine(event)
    snapshot = _partner_b_snapshot(
        [
            _partner_a_run(
                [
                    RecordedAnswer(
                        event_id="duo_choice", question_id="q1", option_id="opt_b"
                    )
                ]
            )
        ]
    )
    loaded = engine.load_game(snapshot)
    selected = engine.select_next_event(loaded)
    assert selected is not None
    assert selected.id == event.id
    resolution = engine.submit_answers(
        loaded, event, [Answer(question_id="q1", option_id="opt_b")]
    )
    session = loaded.session
    assert session.state.finances == 70
    assert session.state.partner_a.simulation_relation_happiness == 75
    assert session.state.partner_b.simulation_relation_happiness == 75
    assert any(
        action.type == "modify_stat"
        and action.args.get("variable") == "compatibility"
        and action.args.get("delta") == 5
        for action in resolution.client_actions
    )
    exported = engine.export_snapshot(loaded)
    assert exported.active_run.answers[0].option_id == "opt_b"
    reloaded = engine.load_game(exported)
    assert reloaded.answer_bank.resolve_for_event(event) == [
        Answer(question_id="q1", option_id="opt_b")
    ]
    assert reloaded.session.answers[0].option_id == "opt_b"


def test_loaded_partner_b_submit_conflict_applies_winner_and_penalties() -> None:
    event = _duo_choice_event()
    engine = _duo_engine(event)
    snapshot = _partner_b_snapshot(
        [
            _partner_a_run(
                [
                    RecordedAnswer(
                        event_id="duo_choice", question_id="q1", option_id="opt_a"
                    )
                ]
            )
        ]
    )
    loaded = engine.load_game(snapshot)
    loaded.session.rng.weighted_choice = MagicMock(return_value="opt_a")
    engine.submit_answers(loaded, event, [Answer(question_id="q1", option_id="opt_b")])
    session = loaded.session
    assert session.state.finances == 51
    assert session.state.partner_a.simulation_relation_happiness == 62
    assert session.state.partner_b.simulation_relation_happiness == 58
    assert session.answers[0].option_id == "opt_b"
    exported = engine.export_snapshot(loaded)
    reloaded = engine.load_game(exported)
    assert reloaded.answer_bank.resolve_for_event(event) == [
        Answer(question_id="q1", option_id="opt_a")
    ]
    assert reloaded.session.answers[0].option_id == "opt_b"


def test_loaded_partner_b_empty_bank_skips_config_deltas() -> None:
    event = _duo_choice_event()
    engine = _duo_engine(event)
    loaded = engine.load_game(_partner_b_snapshot([]))
    engine.submit_answers(loaded, event, [Answer(question_id="q1", option_id="opt_b")])
    session = loaded.session
    assert session.state.finances == 70
    assert session.state.partner_a.simulation_relation_happiness == 70
    assert session.state.partner_b.simulation_relation_happiness == 70
    exported = engine.export_snapshot(loaded)
    reloaded = engine.load_game(exported)
    assert reloaded.answer_bank.resolve_for_event(event) is None
    assert reloaded.session.answers[0].option_id == "opt_b"


def test_session_submit_does_not_use_partner_a_bank() -> None:
    event = _duo_choice_event()
    engine = _duo_engine(event)
    loaded = engine.load_game(
        _partner_b_snapshot(
            [
                _partner_a_run(
                    [
                        RecordedAnswer(
                            event_id="duo_choice",
                            question_id="q1",
                            option_id="opt_a",
                        )
                    ]
                )
            ]
        )
    )
    engine.submit_answers(
        loaded.session, event, [Answer(question_id="q1", option_id="opt_b")]
    )
    session = loaded.session
    assert session.state.finances == 70
    assert session.state.partner_a.simulation_relation_happiness == 70
    assert session.state.partner_b.simulation_relation_happiness == 70
