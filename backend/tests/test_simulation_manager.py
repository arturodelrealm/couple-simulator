import pytest
from couple_simulator_engine.enums import PlayerSex as EnginePlayerSex
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.simulation_run import SimulationRun
from app.schemas.game import GameCreate
from app.services import game_service
from app.services.simulation_manager import SimulationManager
from app.services.simulation_mapper import engine_sex_from_player
from app.shared.enums import PlayerRole, PlayerSex
from app.shared.exceptions import AppError
from app.shared.player_game_stats import GAME_AGE_DEFAULT


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


def test_engine_package_is_importable():
    from couple_simulator_engine import GameEngine

    assert GameEngine is not None


def test_engine_sex_maps_prefer_not_to_say_to_other():
    assert engine_sex_from_player("prefer_not_to_say") == EnginePlayerSex.OTHER
    assert engine_sex_from_player("male") == EnginePlayerSex.MALE
    assert engine_sex_from_player("female") == EnginePlayerSex.FEMALE


def test_start_run_inserts_active_run_and_leaves_lobby_age(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-start-ready", valid_avatar_config)
    manager = SimulationManager()

    view = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=7,
        max_events=5,
    )

    assert view.status == "ACTIVE"
    assert view.player_role == PlayerRole.PARTNER_A.value
    assert view.events_played == 0
    assert view.state["age"] == GAME_AGE_DEFAULT
    assert "finances" in view.state

    partner = db_session.scalar(
        select(Player).where(
            Player.game_id == game.id,
            Player.role == PlayerRole.PARTNER_A.value,
        )
    )
    assert partner is not None
    lobby_age = partner.game_age
    lobby_happiness = partner.game_relation_happiness

    orm_run = db_session.get(SimulationRun, view.run_id)
    assert orm_run is not None
    mutated = dict(orm_run.state_snapshot)
    mutated["partner_a"] = dict(mutated["partner_a"])
    mutated["partner_a"]["simulation_age"] = 40
    orm_run.state_snapshot = mutated
    db_session.commit()

    db_session.refresh(partner)
    assert partner.game_age == lobby_age
    assert partner.game_relation_happiness == lobby_happiness
    assert partner.game_age == GAME_AGE_DEFAULT


def test_two_starts_on_same_game_both_succeed(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-two-starts", valid_avatar_config)
    manager = SimulationManager()

    first = manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value, seed=1)
    second = manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value, seed=2)

    assert first.run_id != second.run_id
    assert first.status == "ACTIVE"
    assert second.status == "ACTIVE"
    assert first.run_number == 1
    assert second.run_number == 2

    rows = list(
        db_session.scalars(
            select(SimulationRun).where(SimulationRun.game_id == game.id),
        )
    )
    assert len(rows) == 2


def test_get_run_round_trips_state_through_load_game(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-get-roundtrip", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=99,
    )

    loaded = manager.get_run(db_session, game.id, started.run_id)

    assert loaded.run_id == started.run_id
    assert loaded.state == started.state
    assert loaded.rng_seed == 99
    assert loaded.answers == []
    assert loaded.timeline == []


def test_start_run_rejects_created_lobby(
    db_session: Session,
):
    game = game_service.create_game(
        db_session,
        GameCreate(match_name="sim-not-ready", partner_a_name="Alex"),
    )
    manager = SimulationManager()

    with pytest.raises(AppError) as exc_info:
        manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value)

    assert exc_info.value.code == "GAME_NOT_READY"
    assert exc_info.value.status_code == 409


def test_start_run_rejects_partner_b_role(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-bad-role", valid_avatar_config)
    manager = SimulationManager()

    with pytest.raises(AppError) as exc_info:
        manager.start_run(db_session, game.id, PlayerRole.PARTNER_B.value)

    assert exc_info.value.code == "INVALID_PLAYER_ROLE"
    assert exc_info.value.status_code == 400


def test_get_run_wrong_game_is_not_found(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    first_game = _create_ready_game(db_session, "sim-game-a", valid_avatar_config)
    second_game = _create_ready_game(db_session, "sim-game-b", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        first_game.id,
        PlayerRole.PARTNER_A.value,
        seed=3,
    )

    with pytest.raises(AppError) as exc_info:
        manager.get_run(db_session, second_game.id, started.run_id)

    assert exc_info.value.code == "RUN_NOT_FOUND"


def test_list_runs_newest_first(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-list-order", valid_avatar_config)
    manager = SimulationManager()
    first = manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value, seed=1)
    second = manager.start_run(db_session, game.id, PlayerRole.PARTNER_A.value, seed=2)

    listed = manager.list_runs(db_session, game.id)

    assert listed.total == 2
    assert [item.run_id for item in listed.items] == [second.run_id, first.run_id]


def test_get_current_event_persists_id_and_repeat_does_not_advance(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-current-event", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=11,
    )
    assert started.current_event_id is None

    first = manager.get_current_event(db_session, game.id, started.run_id)
    assert first.event["event_id"]
    assert first.event["questions"]

    after_first = manager.get_run(db_session, game.id, started.run_id)
    assert after_first.current_event_id == first.event["event_id"]
    events_played = after_first.events_played

    second = manager.get_current_event(db_session, game.id, started.run_id)
    assert second.event["event_id"] == first.event["event_id"]

    after_second = manager.get_run(db_session, game.id, started.run_id)
    assert after_second.events_played == events_played


def test_get_current_event_finished_run_is_conflict(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-finished-event", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=4,
    )
    orm_run = db_session.get(SimulationRun, started.run_id)
    assert orm_run is not None
    orm_run.status = "FINISHED"
    db_session.commit()

    with pytest.raises(AppError) as exc_info:
        manager.get_current_event(db_session, game.id, started.run_id)

    assert exc_info.value.code == "RUN_FINISHED"
    assert exc_info.value.status_code == 409


def _continue_answers(event: dict) -> list[dict[str, str]]:
    answers: list[dict[str, str]] = []
    for question in event["questions"]:
        option_id = question["options"][0]["id"]
        if event["event_id"] == "burnout":
            option_id = next(
                option["id"]
                for option in question["options"]
                if option["id"] == "push_through"
            )
        answers.append(
            {
                "question_id": question["id"],
                "option_id": option_id,
            }
        )
    return answers


def test_submit_answers_persists_and_clears_current_event(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-submit-ok", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=11,
        max_events=5,
    )
    partner = db_session.scalar(
        select(Player).where(
            Player.game_id == game.id,
            Player.role == PlayerRole.PARTNER_A.value,
        )
    )
    assert partner is not None
    lobby_age = partner.game_age

    current = manager.get_current_event(db_session, game.id, started.run_id)
    event_id = current.event["event_id"]
    answers = _continue_answers(current.event)

    result = manager.submit_answers(
        db_session,
        game.id,
        started.run_id,
        event_id,
        answers,
    )

    assert result.run_id == started.run_id
    assert result.events_played == 1
    assert isinstance(result.client_actions, list)
    assert "age" in result.state

    loaded = manager.get_run(db_session, game.id, started.run_id)
    assert loaded.current_event_id is None
    assert loaded.events_played == 1
    assert loaded.answers
    assert all(item["event_id"] == event_id for item in loaded.answers)
    assert len(loaded.answers) == len(answers)

    db_session.refresh(partner)
    assert partner.game_age == lobby_age
    assert partner.game_age == GAME_AGE_DEFAULT

    if result.game_finished or loaded.status == "FINISHED":
        with pytest.raises(AppError) as exc_info:
            manager.get_current_event(db_session, game.id, started.run_id)
        assert exc_info.value.code in {"RUN_FINISHED", "NO_ELIGIBLE_EVENTS"}
        assert exc_info.value.status_code == 409
    else:
        next_event = manager.get_current_event(db_session, game.id, started.run_id)
        assert next_event.event["event_id"] != event_id


def test_submit_answers_rejects_event_mismatch(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-submit-mismatch", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=11,
    )
    current = manager.get_current_event(db_session, game.id, started.run_id)
    answers = _continue_answers(current.event)

    with pytest.raises(AppError) as exc_info:
        manager.submit_answers(
            db_session,
            game.id,
            started.run_id,
            "not_the_open_event",
            answers,
        )

    assert exc_info.value.code == "EVENT_MISMATCH"
    assert exc_info.value.status_code == 409


def test_submit_answers_rejects_finished_run(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-submit-finished", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=4,
    )
    current = manager.get_current_event(db_session, game.id, started.run_id)
    orm_run = db_session.get(SimulationRun, started.run_id)
    assert orm_run is not None
    orm_run.status = "FINISHED"
    db_session.commit()

    with pytest.raises(AppError) as exc_info:
        manager.submit_answers(
            db_session,
            game.id,
            started.run_id,
            current.event["event_id"],
            _continue_answers(current.event),
        )

    assert exc_info.value.code == "RUN_FINISHED"
    assert exc_info.value.status_code == 409


def test_submit_answers_rejects_invalid_answers(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = _create_ready_game(db_session, "sim-submit-invalid", valid_avatar_config)
    manager = SimulationManager()
    started = manager.start_run(
        db_session,
        game.id,
        PlayerRole.PARTNER_A.value,
        seed=11,
    )
    current = manager.get_current_event(db_session, game.id, started.run_id)

    with pytest.raises(AppError) as exc_info:
        manager.submit_answers(
            db_session,
            game.id,
            started.run_id,
            current.event["event_id"],
            [],
        )

    assert exc_info.value.code == "INVALID_ANSWERS"
    assert exc_info.value.status_code == 409
