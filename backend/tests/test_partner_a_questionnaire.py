from uuid import uuid4

import pytest
from couple_simulator_engine.state import SimulationState
from sqlalchemy.orm import Session

from app.models.simulation_answer import SimulationAnswer
from app.models.simulation_run import SimulationRun
from app.models.timeline_entry import TimelineEntry
from app.schemas.game import GameCreate
from app.services import game_service
from app.services.partner_a_questionnaire import get_or_create_prep_run
from app.services.simulation_manager import SimulationManager
from app.shared.enums import (
    PlayerRole,
    PlayerSex,
    SimulationRunKind,
    SimulationRunStatus,
)
from app.shared.exceptions import AppError


def _create_ready_game(db: Session, match_name: str, avatar: dict[str, str]):
    return game_service.create_game(
        db,
        GameCreate(
            match_name=match_name,
            partner_a_name="Alex",
            partner_a_sex=PlayerSex.FEMALE,
            avatar_config=avatar,
        ),
    )


def test_get_or_create_prep_run_is_idempotent(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "prep-idempotent", valid_avatar_config)

    first = get_or_create_prep_run(db_session, game.id)
    second = get_or_create_prep_run(db_session, game.id)

    assert first.id == second.id
    assert first.run_kind == SimulationRunKind.QUESTIONNAIRE.value
    assert first.player_role == PlayerRole.PARTNER_A.value
    assert first.status == SimulationRunStatus.ACTIVE.value
    assert first.events_played == 0
    assert first.skipped_event_ids == []


def test_empty_prep_seeds_last_write_wins_from_simulation_runs(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "prep-legacy-seed", valid_avatar_config)
    manager = SimulationManager()
    first_sim = manager.start_run(
        db_session, game.id, PlayerRole.PARTNER_A.value, seed=1
    )
    second_sim = manager.start_run(
        db_session, game.id, PlayerRole.PARTNER_A.value, seed=2
    )

    first_run = db_session.get(SimulationRun, first_sim.run_id)
    second_run = db_session.get(SimulationRun, second_sim.run_id)
    assert first_run is not None
    assert second_run is not None
    first_run.answers.append(
        SimulationAnswer(
            event_id="evt-1",
            question_id="q-1",
            option_id="opt-first",
            sort_index=0,
        ),
    )
    first_run.answers.append(
        SimulationAnswer(
            event_id="evt-2",
            question_id="q-2",
            option_id="opt-keep",
            sort_index=1,
        ),
    )
    second_run.answers.append(
        SimulationAnswer(
            event_id="evt-1",
            question_id="q-1",
            option_id="opt-last",
            sort_index=0,
        ),
    )
    second_run.timeline_entries.append(
        TimelineEntry(
            title="Should not copy",
            category="life",
            age=22,
            description="legacy",
            sort_index=0,
        ),
    )
    mutated = dict(second_run.state_snapshot)
    mutated["finances"] = 11
    second_run.state_snapshot = mutated
    db_session.commit()

    prep = get_or_create_prep_run(db_session, game.id)
    defaults = SimulationState()

    by_key = {
        (item.event_id, item.question_id): item.option_id for item in prep.answers
    }
    assert by_key[("evt-1", "q-1")] == "opt-last"
    assert by_key[("evt-2", "q-2")] == "opt-keep"
    assert len(prep.answers) == 2
    assert prep.timeline_entries == []
    assert prep.events_played == 0
    assert prep.state_snapshot["finances"] == defaults.finances
    assert prep.state_snapshot["finances"] != 11


def test_seed_does_not_change_prep_stats_or_timeline(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(
        db_session, "prep-no-sim-side-effects", valid_avatar_config
    )
    manager = SimulationManager()
    sim = manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value, seed=8)
    sim_run = db_session.get(SimulationRun, sim.run_id)
    assert sim_run is not None
    sim_run.answers.append(
        SimulationAnswer(
            event_id="evt-stat",
            question_id="q-stat",
            option_id="opt-stat",
            sort_index=0,
        ),
    )
    db_session.commit()

    prep = get_or_create_prep_run(db_session, game.id)
    defaults = SimulationState()
    assert prep.timeline_entries == []
    assert prep.state_snapshot["finances"] == defaults.finances
    assert prep.state_snapshot["quality_of_life"] == defaults.quality_of_life
    assert prep.events_played == 0


def test_get_or_create_prep_run_unknown_game(db_session: Session):
    with pytest.raises(AppError) as exc_info:
        get_or_create_prep_run(db_session, uuid4())
    assert exc_info.value.code == "GAME_NOT_FOUND"


def test_get_or_create_prep_run_not_ready(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="prep-not-ready", partner_a_name="Alex"),
    )
    with pytest.raises(AppError) as exc_info:
        get_or_create_prep_run(db_session, created.id)
    assert exc_info.value.code == "GAME_NOT_READY"
