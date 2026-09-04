"""Round-trip tests for GameSnapshot helpers (no GameEngine)."""

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.resolution.post_event_economy import (
    apply_post_event_economy,
)
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import GameSession, RecordedAnswer, TimelineEntry
from couple_simulator_engine.snapshot import (
    GameSnapshot,
    RunSnapshot,
    copy_simulation_state,
    export_loaded_game,
    hydrate_loaded_game,
)
from couple_simulator_engine.state import SimulationState


def _partner(name: str, *, game_age: int, sim_age: int) -> Player:
    return Player(
        id=name.lower().replace(" ", "_"),
        name=name,
        sex=PlayerSex.FEMALE,
        game_age=game_age,
        game_relation_happiness=80,
        simulation_age=sim_age,
        simulation_relation_happiness=70,
        avatar_config={"hair": "short"},
    )


def _state() -> SimulationState:
    return SimulationState(
        partner_a=_partner("Alex", game_age=28, sim_age=29),
        partner_b=_partner("Sam", game_age=26, sim_age=27),
        finances=40,
        quality_of_life=45,
        children=1,
    )


def _active_run(*, answers: list[RecordedAnswer] | None = None) -> RunSnapshot:
    return RunSnapshot(
        run_id="run-active",
        player_role="partner_a",
        run_number=2,
        status=SessionStatus.ACTIVE,
        rng_seed=42,
        events_played=1,
        events_played_ids=["weekend_trip"],
        timeline=[
            TimelineEntry(
                title="Trip",
                category="adventure",
                age=29,
                description="Went away",
            )
        ],
        answers=answers
        if answers is not None
        else [
            RecordedAnswer(
                event_id="weekend_trip",
                question_id="go",
                option_id="yes",
                state_snapshot={"finances": 40},
            )
        ],
        event_variables={"flag": 1},
        current_event_id="buy_house_light",
        end_reason=None,
        max_events=5,
        state=_state(),
    )


def _past_a_run() -> RunSnapshot:
    return RunSnapshot(
        run_id="run-past",
        player_role="partner_a",
        run_number=1,
        status=SessionStatus.FINISHED,
        rng_seed=7,
        events_played=1,
        events_played_ids=["burnout"],
        timeline=[],
        answers=[
            RecordedAnswer(
                event_id="burnout",
                question_id="burnout_choice",
                option_id="push_through",
            )
        ],
        event_variables={},
        current_event_id=None,
        end_reason="max_events",
        max_events=5,
    )


def _snapshot() -> GameSnapshot:
    return GameSnapshot(
        game_id="game-1",
        mode="solo",
        active_run=_active_run(),
        partner_a_runs=[_past_a_run()],
        config=GameConfig(max_events=5),
    )


def _assert_players_equal(left: Player, right: Player) -> None:
    assert left.id == right.id
    assert left.name == right.name
    assert left.sex == right.sex
    assert left.game_age == right.game_age
    assert left.game_relation_happiness == right.game_relation_happiness
    assert left.simulation_age == right.simulation_age
    assert left.simulation_relation_happiness == right.simulation_relation_happiness
    assert left.avatar_config == right.avatar_config


def _assert_states_equal(left: SimulationState, right: SimulationState) -> None:
    _assert_players_equal(left.partner_a, right.partner_a)
    _assert_players_equal(left.partner_b, right.partner_b)
    assert left.finances == right.finances
    assert left.quality_of_life == right.quality_of_life
    assert left.children == right.children
    assert left.wellness == right.wellness
    assert left.housing == right.housing
    assert left.mascot == right.mascot
    assert left.tags == right.tags
    assert left.life_stage == right.life_stage
    assert left.relationship_status == right.relationship_status
    assert left.age == right.age
    assert left.compatibility == right.compatibility


def _assert_runs_equal(left: RunSnapshot, right: RunSnapshot) -> None:
    assert left.run_id == right.run_id
    assert left.player_role == right.player_role
    assert left.run_number == right.run_number
    assert left.status == right.status
    assert left.rng_seed == right.rng_seed
    assert left.events_played == right.events_played
    assert left.events_played_ids == right.events_played_ids
    assert left.timeline == right.timeline
    assert left.event_variables == right.event_variables
    assert left.current_event_id == right.current_event_id
    assert left.end_reason == right.end_reason
    assert left.max_events == right.max_events
    _assert_states_equal(left.state, right.state)
    assert len(left.answers) == len(right.answers)
    for left_answer, right_answer in zip(left.answers, right.answers, strict=True):
        assert left_answer.event_id == right_answer.event_id
        assert left_answer.question_id == right_answer.question_id
        assert left_answer.option_id == right_answer.option_id
        assert right_answer.state_snapshot is None


def test_hydrate_active_run_restores_session_fields() -> None:
    snapshot = _snapshot()
    loaded = hydrate_loaded_game(snapshot)
    session = loaded.session
    assert session.rng.seed == snapshot.active_run.rng_seed
    _assert_states_equal(session.state, snapshot.active_run.state)
    assert session.timeline == snapshot.active_run.timeline
    assert len(session.answers) == len(snapshot.active_run.answers)
    assert session.answers[0].option_id == "yes"
    assert session.current_event_id == "buy_house_light"
    assert session.events_played == 1
    assert session.player.name == "Alex"
    assert loaded.prefer_answer_bank_events is False


def test_answer_bank_unions_partner_a_runs_and_active_a_answers() -> None:
    snapshot = _snapshot()
    loaded = hydrate_loaded_game(snapshot)
    bank = loaded.answer_bank
    event_ids = {entry.event_id for entry in bank.entries}
    assert event_ids == {"weekend_trip", "burnout"}
    weekend = EventDefinition(
        id="weekend_trip",
        title="Weekend",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="go",
                text="Go?",
                options=(OptionDefinition(id="yes", text="Yes"),),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )
    burnout = EventDefinition(
        id="burnout",
        title="Burnout",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="burnout_choice",
                text="How?",
                options=(OptionDefinition(id="push_through", text="Push"),),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )
    assert bank.has_coverage_for(weekend) is True
    assert bank.has_coverage_for(burnout) is True


def test_export_then_hydrate_is_lossless_except_answer_state_snapshot() -> None:
    original = _snapshot()
    exported = export_loaded_game(hydrate_loaded_game(original))
    assert exported.game_id == original.game_id
    assert exported.mode == original.mode
    assert exported.config == original.config
    _assert_runs_equal(original.active_run, exported.active_run)
    assert len(exported.partner_a_runs) == 1
    assert exported.partner_a_runs[0].run_id == original.partner_a_runs[0].run_id
    assert exported.partner_a_runs[0].answers[0].option_id == "push_through"
    second = export_loaded_game(hydrate_loaded_game(exported))
    _assert_runs_equal(second.active_run, exported.active_run)
    assert original.active_run.answers[0].state_snapshot == {"finances": 40}
    assert exported.active_run.answers[0].state_snapshot is None


def test_snapshot_preserves_finances_and_income_band_after_passive_tick() -> None:
    state = _state()
    state.tags["income_band"] = "high"
    session = GameSession(
        session_id="econ-snap",
        player=state.partner_a,
        state=state,
        config=GameConfig(),
        rng=SeededRNG(1),
    )
    apply_post_event_economy(session, game_finished=False)
    assert session.state.finances == 46
    copied = copy_simulation_state(session.state)
    assert copied.finances == 46
    assert copied.tags == {"income_band": "high"}

    snapshot = GameSnapshot(
        game_id="game-econ",
        mode="solo",
        active_run=RunSnapshot(
            run_id="run-econ",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=1,
            events_played=1,
            events_played_ids=["noop_tick"],
            timeline=[],
            answers=[],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
            state=copied,
        ),
        partner_a_runs=[],
        config=GameConfig(),
    )
    loaded = hydrate_loaded_game(snapshot)
    assert loaded.session.state.finances == 46
    assert loaded.session.state.tags == {"income_band": "high"}
    exported = export_loaded_game(loaded)
    assert exported.active_run.state.finances == 46
    assert exported.active_run.state.tags == {"income_band": "high"}
