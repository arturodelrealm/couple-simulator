import pytest
from sqlalchemy.orm import Session

from app.schemas.game import GameCreate, GameUpdate
from app.services import game_service
from app.shared.enums import GameStatus, PlayerSex
from app.shared.exceptions import AppError


def test_create_game_stores_match_name_and_optional_partner_a(db_session: Session):
    game = game_service.create_game(
        db_session,
        GameCreate(
            match_name="boda-ana-luis",
            game_mode="couple",
            partner_a_name="Alex",
        ),
    )

    assert game.match_name == "boda-ana-luis"
    assert game.game_mode == "couple"
    assert game.partner_a.name == "Alex"
    assert game.status == GameStatus.CREATED.value
    assert game.partner_a.avatar_config is None
    assert game.partner_a.sex is None
    assert game.partner_a.game_age == 22
    assert game.partner_a.game_relation_happiness == 100


def test_create_game_with_complete_setup_is_player_a_ready(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game = game_service.create_game(
        db_session,
        GameCreate(
            match_name="complete-setup",
            partner_a_name="Alex",
            partner_a_sex=PlayerSex.FEMALE,
            avatar_config=valid_avatar_config,
        ),
    )

    assert game.status == GameStatus.PLAYER_A_READY.value
    assert game.partner_a.sex == PlayerSex.FEMALE.value
    assert game.partner_a.avatar_config == valid_avatar_config


def test_create_game_raises_match_name_taken(db_session: Session):
    game_service.create_game(
        db_session,
        GameCreate(match_name="Boda"),
    )

    with pytest.raises(AppError) as exc_info:
        game_service.create_game(
            db_session,
            GameCreate(match_name="boda"),
        )

    assert exc_info.value.code == "MATCH_NAME_TAKEN"
    assert exc_info.value.status_code == 409


def test_get_game_by_match_name(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="find-me"),
    )

    found = game_service.get_game_by_match_name(db_session, "Find-Me")

    assert found.id == created.id
    assert found.match_name == "find-me"


def test_get_game_by_match_name_raises_not_found(db_session: Session):
    with pytest.raises(AppError) as exc_info:
        game_service.get_game_by_match_name(db_session, "missing-game")

    assert exc_info.value.code == "GAME_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_update_game_sets_player_a_ready_when_name_avatar_and_sex_present(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    created = game_service.create_game(
        db_session,
        GameCreate(
            match_name="update-ready",
            partner_a_name="Alex",
        ),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(
            avatar_config=valid_avatar_config,
            partner_a_sex=PlayerSex.MALE,
        ),
    )

    assert updated.status == GameStatus.PLAYER_A_READY.value
    assert updated.partner_a.avatar_config == valid_avatar_config
    assert updated.partner_a.sex == PlayerSex.MALE.value


def test_update_game_keeps_created_without_avatar(
    db_session: Session,
):
    created = game_service.create_game(
        db_session,
        GameCreate(
            match_name="no-avatar",
            partner_a_name="Alex",
        ),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(partner_a_name="Jordan"),
    )

    assert updated.status == GameStatus.CREATED.value
    assert updated.partner_a.name == "Jordan"
    assert updated.partner_a.avatar_config is None


def test_update_game_partner_a_sex_only_keeps_created_without_other_fields(
    db_session: Session,
):
    created = game_service.create_game(
        db_session,
        GameCreate(
            match_name="sex-only",
            partner_a_name="Alex",
        ),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(partner_a_sex=PlayerSex.FEMALE),
    )

    assert updated.status == GameStatus.CREATED.value
    assert updated.partner_a.sex == PlayerSex.FEMALE.value


def test_update_game_rejects_empty_payload(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="empty-patch", partner_a_name="Alex"),
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


def test_get_game_invite_returns_path_and_url(db_session: Session):
    game = game_service.create_game(
        db_session,
        GameCreate(match_name="share-me"),
    )

    invite = game_service.get_game_invite(
        db_session,
        game.id,
        frontend_public_url="https://app.example.com",
    )

    assert invite.game_id == game.id
    assert invite.match_name == "share-me"
    assert invite.invite_path == "/games/join/share-me"
    assert invite.invite_url == "https://app.example.com/games/join/share-me"


def test_create_game_with_custom_game_stats(db_session: Session):
    game = game_service.create_game(
        db_session,
        GameCreate(
            match_name="custom-stats",
            partner_a_game_age=30,
            partner_a_game_relation_happiness=80,
        ),
    )

    assert game.partner_a.game_age == 30
    assert game.partner_a.game_relation_happiness == 80
    assert game.status == GameStatus.CREATED.value


def test_create_game_rejects_game_age_below_18(db_session: Session):
    with pytest.raises(AppError) as exc_info:
        game_service.create_game(
            db_session,
            GameCreate(match_name="too-young", partner_a_game_age=17),
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert exc_info.value.status_code == 400
    assert exc_info.value.field == "body.partner_a_game_age"


def test_create_game_rejects_happiness_out_of_range(db_session: Session):
    with pytest.raises(AppError) as exc_info:
        game_service.create_game(
            db_session,
            GameCreate(
                match_name="too-happy",
                partner_a_game_relation_happiness=101,
            ),
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert exc_info.value.field == "body.partner_a_game_relation_happiness"


def test_update_game_stats_only_does_not_require_name_sex_or_avatar(
    db_session: Session,
):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="stats-only-patch"),
    )

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(
            partner_a_game_age=25,
            partner_a_game_relation_happiness=40,
        ),
    )

    assert updated.partner_a.game_age == 25
    assert updated.partner_a.game_relation_happiness == 40
    assert updated.status == GameStatus.CREATED.value
    assert updated.partner_a.name is None
    assert updated.partner_a.sex is None
    assert updated.partner_a.avatar_config is None


def test_update_game_stats_does_not_make_player_a_ready_without_setup(
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    created = game_service.create_game(
        db_session,
        GameCreate(
            match_name="stats-not-ready",
            partner_a_name="Alex",
            partner_a_sex=PlayerSex.MALE,
            avatar_config=valid_avatar_config,
        ),
    )
    assert created.status == GameStatus.PLAYER_A_READY.value

    updated = game_service.update_game(
        db_session,
        created.id,
        GameUpdate(partner_a_game_age=40),
    )

    assert updated.status == GameStatus.PLAYER_A_READY.value
    assert updated.partner_a.game_age == 40
    assert updated.partner_a.name == "Alex"


def test_update_game_rejects_invalid_game_age(db_session: Session):
    created = game_service.create_game(
        db_session,
        GameCreate(match_name="invalid-age-patch"),
    )

    with pytest.raises(AppError) as exc_info:
        game_service.update_game(
            db_session,
            created.id,
            GameUpdate(partner_a_game_age=10),
        )

    assert exc_info.value.code == "VALIDATION_ERROR"
    assert exc_info.value.field == "body.partner_a_game_age"
