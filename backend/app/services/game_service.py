from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.avatar_config import AvatarConfig
from app.models.game import Game
from app.models.player import Player
from app.schemas.game import (
    GameCreate,
    GameInviteRead,
    GameRead,
    GameUpdate,
    PartnerARead,
)
from app.shared.avatar_validation import validate_avatar_config
from app.shared.enums import GameStatus, PlayerRole
from app.shared.exceptions import AppError
from app.shared.game_invite import build_invite_path, build_invite_url
from app.shared.i18n import translate as _
from app.shared.match_name_validation import validate_match_name
from app.shared.player_game_stats import (
    GAME_AGE_DEFAULT,
    GAME_RELATION_HAPPINESS_DEFAULT,
    validate_game_age,
    validate_game_relation_happiness,
)


def _partner_a_from_game(game: Game) -> PartnerARead:
    partner_a = next(
        (p for p in game.players if p.role == PlayerRole.PARTNER_A.value),
        None,
    )
    if partner_a is None:
        return PartnerARead(
            name=None,
            sex=None,
            avatar_config=None,
            game_age=GAME_AGE_DEFAULT,
            game_relation_happiness=GAME_RELATION_HAPPINESS_DEFAULT,
        )

    avatar_config: dict[str, Any] | None = None
    if partner_a.avatar_config is not None:
        avatar_config = partner_a.avatar_config.config

    return PartnerARead(
        name=partner_a.name,
        sex=partner_a.sex,
        avatar_config=avatar_config,
        game_age=partner_a.game_age,
        game_relation_happiness=partner_a.game_relation_happiness,
    )


def _game_to_read(game: Game) -> GameRead:
    return GameRead(
        id=game.id,
        match_name=game.match_name,
        game_mode=game.game_mode,
        status=game.status,
        partner_a=_partner_a_from_game(game),
    )


def _get_partner_a(game: Game) -> Player:
    partner_a = next(
        (p for p in game.players if p.role == PlayerRole.PARTNER_A.value),
        None,
    )
    if partner_a is None:
        raise AppError(
            "INTERNAL_ERROR",
            _("Partner A not found for this game"),
            status_code=500,
        )
    return partner_a


def _apply_status(game: Game, partner_a: Player) -> None:
    has_name = partner_a.name is not None and partner_a.name.strip() != ""
    has_avatar = partner_a.avatar_config is not None
    has_sex = partner_a.sex is not None
    if has_name and has_avatar and has_sex:
        game.status = GameStatus.PLAYER_A_READY.value
    else:
        game.status = GameStatus.CREATED.value


def _load_game_with_players(db: Session, game_id: UUID) -> Game | None:
    return db.scalar(
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.players).selectinload(Player.avatar_config),
        ),
    )


def get_game(db: Session, game_id: UUID) -> GameRead:
    game = _load_game_with_players(db, game_id)
    if game is None:
        raise AppError(
            "GAME_NOT_FOUND",
            _("Game not found"),
            status_code=404,
        )
    return _game_to_read(game)


def get_game_by_match_name(db: Session, match_name: str) -> GameRead:
    normalized = validate_match_name(match_name, field="path.match_name")
    game = db.scalar(
        select(Game)
        .where(Game.match_name == normalized)
        .options(
            selectinload(Game.players).selectinload(Player.avatar_config),
        ),
    )
    if game is None:
        raise AppError(
            "GAME_NOT_FOUND",
            _("Game not found"),
            status_code=404,
        )
    return _game_to_read(game)


def create_game(db: Session, payload: GameCreate) -> GameRead:
    existing = db.scalar(
        select(Game).where(Game.match_name == payload.match_name),
    )
    if existing is not None:
        raise AppError(
            "MATCH_NAME_TAKEN",
            _("Match name is already taken"),
            status_code=409,
        )

    game = Game(
        match_name=payload.match_name,
        game_mode=payload.game_mode.value,
        status=GameStatus.CREATED.value,
    )
    game_age = GAME_AGE_DEFAULT
    if payload.partner_a_game_age is not None:
        game_age = validate_game_age(
            payload.partner_a_game_age,
            field="body.partner_a_game_age",
        )

    game_relation_happiness = GAME_RELATION_HAPPINESS_DEFAULT
    if payload.partner_a_game_relation_happiness is not None:
        game_relation_happiness = validate_game_relation_happiness(
            payload.partner_a_game_relation_happiness,
            field="body.partner_a_game_relation_happiness",
        )

    partner_a = Player(
        role=PlayerRole.PARTNER_A.value,
        name=payload.partner_a_name,
        sex=payload.partner_a_sex.value if payload.partner_a_sex is not None else None,
        game_age=game_age,
        game_relation_happiness=game_relation_happiness,
    )

    if payload.avatar_config is not None:
        validated = validate_avatar_config(payload.avatar_config)
        partner_a.avatar_config = AvatarConfig(config=validated)

    game.players.append(partner_a)
    _apply_status(game, partner_a)
    db.add(game)
    db.commit()
    return get_game(db, game.id)


def update_game(db: Session, game_id: UUID, payload: GameUpdate) -> GameRead:
    if (
        payload.partner_a_name is None
        and payload.partner_a_sex is None
        and payload.avatar_config is None
        and payload.partner_a_game_age is None
        and payload.partner_a_game_relation_happiness is None
    ):
        raise AppError(
            "BAD_REQUEST",
            _("At least one field must be provided"),
            status_code=400,
        )

    game = _load_game_with_players(db, game_id)
    if game is None:
        raise AppError(
            "GAME_NOT_FOUND",
            _("Game not found"),
            status_code=404,
        )

    partner_a = _get_partner_a(game)

    if payload.partner_a_name is not None:
        partner_a.name = payload.partner_a_name

    if payload.partner_a_sex is not None:
        partner_a.sex = payload.partner_a_sex.value

    if payload.avatar_config is not None:
        validated = validate_avatar_config(payload.avatar_config)
        if partner_a.avatar_config is None:
            partner_a.avatar_config = AvatarConfig(config=validated)
        else:
            partner_a.avatar_config.config = validated

    if payload.partner_a_game_age is not None:
        partner_a.game_age = validate_game_age(
            payload.partner_a_game_age,
            field="body.partner_a_game_age",
        )

    if payload.partner_a_game_relation_happiness is not None:
        partner_a.game_relation_happiness = validate_game_relation_happiness(
            payload.partner_a_game_relation_happiness,
            field="body.partner_a_game_relation_happiness",
        )

    _apply_status(game, partner_a)
    db.commit()
    return get_game(db, game_id)


def get_game_invite(
    db: Session,
    game_id: UUID,
    *,
    frontend_public_url: str | None = None,
) -> GameInviteRead:
    game = get_game(db, game_id)
    invite_path = build_invite_path(game.match_name)
    return GameInviteRead(
        game_id=game.id,
        match_name=game.match_name,
        invite_path=invite_path,
        invite_url=build_invite_url(invite_path, frontend_public_url),
    )
