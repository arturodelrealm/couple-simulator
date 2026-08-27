import pytest
from sqlalchemy.orm import Session

from app.schemas.game import GameCreate, GameUpdate
from app.services import game_service
from app.shared.enums import GameStatus
from app.shared.exceptions import AppError


def test_create_game_stores_partner_a_name(db_session: Session):
    game = game_service.create_game(
        db_session,
        GameCreate(partner_a_name="Alex"),
    )

    assert game.partner_a.name == "Alex"
    assert game.status == GameStatus.CREATED.value
    assert game.partner_a.avatar_config is None


def test_update_game_sets_player_a_ready_when_name_and_avatar_present(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    created = game_service.create_game(
        db_session,
        GameCreate(partner_a_name="Alex"),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(avatar_config=valid_avatar_config),
    )

    assert updated.status == GameStatus.PLAYER_A_READY.value
    assert updated.partner_a.avatar_config == valid_avatar_config


def test_update_game_keeps_created_without_avatar(
    db_session: Session,
):
    created = game_service.create_game(
        db_session,
        GameCreate(partner_a_name="Alex"),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(partner_a_name="Jordan"),
    )

    assert updated.status == GameStatus.CREATED.value
    assert updated.partner_a.name == "Jordan"
    assert updated.partner_a.avatar_config is None


def test_update_game_rejects_empty_payload(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(partner_a_name="Alex"),
    )

    with pytest.raises(AppError) as exc_info:
        game_service.update_game(db_session, created.id, GameUpdate())

    assert exc_info.value.code == "BAD_REQUEST"
    assert exc_info.value.status_code == 400


def test_get_game_raises_not_found(db_session: Session):
    from uuid import uuid4

    with pytest.raises(AppError) as exc_info:
        game_service.get_game(db_session, uuid4())

    assert exc_info.value.code == "GAME_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_update_game_raises_not_found(db_session: Session):
    from uuid import uuid4

    with pytest.raises(AppError) as exc_info:
        game_service.update_game(
            db_session,
            uuid4(),
            GameUpdate(partner_a_name="Alex"),
        )

    assert exc_info.value.code == "GAME_NOT_FOUND"
    assert exc_info.value.status_code == 404
