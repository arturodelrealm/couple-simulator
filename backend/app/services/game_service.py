from gettext import gettext as _
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.avatar_config import AvatarConfig
from app.models.game import Game
from app.models.player import Player
from app.schemas.game import GameCreate, GameRead, GameUpdate, PartnerARead
from app.shared.avatar_validation import validate_avatar_config
from app.shared.enums import GameStatus, PlayerRole
from app.shared.exceptions import AppError


def _partner_a_from_game(game: Game) -> PartnerARead:
    partner_a = next(
        (p for p in game.players if p.role == PlayerRole.PARTNER_A.value),
        None,
    )
    if partner_a is None:
        return PartnerARead(name=None, avatar_config=None)

    avatar_config: dict[str, Any] | None = None
    if partner_a.avatar_config is not None:
        avatar_config = partner_a.avatar_config.config

    return PartnerARead(name=partner_a.name, avatar_config=avatar_config)


def _game_to_read(game: Game) -> GameRead:
    return GameRead(
        id=game.id,
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
    if has_name and has_avatar:
        game.status = GameStatus.PLAYER_A_READY.value
    else:
        game.status = GameStatus.CREATED.value


def get_game(db: Session, game_id: UUID) -> GameRead:
    game = db.scalar(
        select(Game)
        .where(Game.id == game_id)
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
    game = Game(status=GameStatus.CREATED.value)
    partner_a = Player(
        role=PlayerRole.PARTNER_A.value,
        name=payload.partner_a_name,
    )
    game.players.append(partner_a)
    db.add(game)
    db.commit()
    db.refresh(game)
    return get_game(db, game.id)


def update_game(db: Session, game_id: UUID, payload: GameUpdate) -> GameRead:
    if payload.partner_a_name is None and payload.avatar_config is None:
        raise AppError(
            "BAD_REQUEST",
            _("At least one field must be provided"),
            status_code=400,
        )

    game = db.scalar(
        select(Game)
        .where(Game.id == game_id)
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

    partner_a = _get_partner_a(game)

    if payload.partner_a_name is not None:
        partner_a.name = payload.partner_a_name

    if payload.avatar_config is not None:
        validated = validate_avatar_config(payload.avatar_config)
        if partner_a.avatar_config is None:
            partner_a.avatar_config = AvatarConfig(config=validated)
        else:
            partner_a.avatar_config.config = validated

    _apply_status(game, partner_a)
    db.commit()
    return get_game(db, game_id)
