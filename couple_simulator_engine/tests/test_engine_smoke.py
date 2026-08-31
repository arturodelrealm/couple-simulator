"""Programmatic GameEngine smoke tests (no CLI)."""

from pathlib import Path

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import (
    ContentCatalog,
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.engine import END_REASON_MAX_EVENTS, GameEngine
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.session import Answer, GameSession

FIXED_SEED = 42
PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "couple_simulator_engine"


def _player() -> Player:
    return Player(id="p1", name="Alex", sex=PlayerSex.OTHER)


def _continue_answers(event: EventDefinition) -> list[Answer]:
    """Pick options that do not trigger ``end_game`` (burnout quit)."""
    answers: list[Answer] = []
    for question in event.questions:
        option_id = question.options[0].id
        if event.id == "burnout":
            option_id = next(
                option.id for option in question.options if option.id == "push_through"
            )
        answers.append(Answer(question_id=question.id, option_id=option_id))
    return answers


def _run_until_finished(engine: GameEngine, session: GameSession) -> None:
    while not engine.check_end_conditions(session).finished:
        event = engine.select_next_event(session)
        if event is None:
            engine.check_end_conditions(session)
            break
        engine.present_event(event)
        engine.submit_answers(session, event, _continue_answers(event))


def test_full_session_plays_at_least_three_events_with_fixed_seed() -> None:
    catalog = load_catalog(package_events_directory())
    engine = GameEngine(catalog, GameConfig(max_events=5))
    session = engine.new_session(_player(), seed=FIXED_SEED)
    _run_until_finished(engine, session)
    assert session.events_played >= 3
    assert session.status == SessionStatus.FINISHED
    summary = engine.build_summary(session)
    assert summary.events_played == session.events_played
    assert summary.end_reason is not None


def test_session_ends_when_max_events_reached() -> None:
    catalog = load_catalog(package_events_directory())
    engine = GameEngine(catalog, GameConfig(max_events=3))
    session = engine.new_session(_player(), seed=FIXED_SEED)
    _run_until_finished(engine, session)
    assert session.events_played == 3
    assert session.status == SessionStatus.FINISHED
    assert session.end_reason == END_REASON_MAX_EVENTS
    assert engine.check_end_conditions(session).finished is True


def test_burnout_end_game_finishes_session_early() -> None:
    catalog = load_catalog(package_events_directory())
    burnout = catalog.get("burnout")
    assert burnout is not None
    engine = GameEngine(ContentCatalog([burnout]), GameConfig(max_events=5))
    session = engine.new_session(_player(), seed=FIXED_SEED)
    event = engine.select_next_event(session)
    assert event is not None
    assert event.id == "burnout"
    resolution = engine.submit_answers(
        session,
        event,
        [Answer(question_id="burnout_choice", option_id="quit_job")],
    )
    assert resolution.game_finished is True
    end = engine.check_end_conditions(session)
    assert end.finished is True
    assert session.status == SessionStatus.FINISHED
    assert session.end_reason == "burnout"
    assert session.events_played == 1
    assert session.events_played < session.config.max_events


def test_fixed_seed_smoke_finishes_with_events_played() -> None:
    catalog = load_catalog(package_events_directory())
    engine = GameEngine(catalog)
    session = engine.new_session(_player(), seed=FIXED_SEED)
    _run_until_finished(engine, session)
    assert session.events_played >= 1
    assert session.status == SessionStatus.FINISHED


def test_core_package_has_no_print() -> None:
    offenders: list[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("print(") or stripped.startswith("print "):
                offenders.append(f"{path}:{line_no}:{line.strip()}")
    assert offenders == []
