from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.models import (
    Game,
    SimulationAnswer,
    SimulationRun,
    TimelineEntry,
)
from app.schemas.game import GameCreate
from app.services import game_service
from app.shared.enums import PlayerRole, SimulationRunStatus


def _add_run(
    db: Session,
    game: Game,
    *,
    run_number: int,
    status: str = SimulationRunStatus.ACTIVE.value,
) -> SimulationRun:
    run = SimulationRun(
        player_role=PlayerRole.PARTNER_A.value,
        run_number=run_number,
        status=status,
        rng_seed=42,
        max_events=10,
        state_snapshot={"couple": {"finances": 50}},
        events_played_ids=[],
        event_variables={},
    )
    game.simulation_runs.append(run)
    return run


def test_metadata_includes_simulation_tables():
    table_names = set(inspect(Game).mapper.local_table.metadata.tables)
    assert "simulation_runs" in table_names
    assert "simulation_answers" in table_names
    assert "timeline_entries" in table_names


def test_two_active_runs_same_game_and_role_are_allowed(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="two-active-runs"),
    )
    game = db_session.get(Game, created.id)
    assert game is not None

    first = _add_run(db_session, game, run_number=1)
    second = _add_run(db_session, game, run_number=2)
    db_session.commit()

    runs = list(
        db_session.scalars(
            select(SimulationRun).where(SimulationRun.game_id == game.id),
        ),
    )
    assert len(runs) == 2
    assert {run.id for run in runs} == {first.id, second.id}
    assert all(run.status == SimulationRunStatus.ACTIVE.value for run in runs)
    assert all(run.player_role == PlayerRole.PARTNER_A.value for run in runs)


def test_deleting_game_cascades_to_runs_answers_and_timeline(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="cascade-delete-run"),
    )
    game = db_session.get(Game, created.id)
    assert game is not None

    run = _add_run(db_session, game, run_number=1)
    run.answers.append(
        SimulationAnswer(
            event_id="evt-1",
            question_id="q-1",
            option_id="opt-a",
            sort_index=0,
        ),
    )
    run.timeline_entries.append(
        TimelineEntry(
            title="Moved in",
            category="life",
            age=22,
            description="First apartment",
            sort_index=0,
        ),
    )
    db_session.commit()

    run_id = run.id
    db_session.delete(game)
    db_session.commit()

    assert db_session.get(Game, created.id) is None
    assert db_session.get(SimulationRun, run_id) is None
    assert db_session.scalar(select(SimulationAnswer)) is None
    assert db_session.scalar(select(TimelineEntry)) is None
