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
    PartnerRead,
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


def _partner_read_from_player(player: Player) -> PartnerRead:
    avatar_config: dict[str, Any] | None = None
    if player.avatar_config is not None:
        avatar_config = player.avatar_config.config
    return PartnerRead(
        name=player.name,
        sex=player.sex,
        avatar_config=avatar_config,
        game_age=player.game_age,
        game_relation_happiness=player.game_relation_happiness,
    )


def _player_by_role(game: Game, role: PlayerRole) -> Player | None:
    return next(
        (player for player in game.players if player.role == role.value),
        None,
    )


def _partner_a_from_game(game: Game) -> PartnerRead:
    partner_a = _player_by_role(game, PlayerRole.PARTNER_A)
    if partner_a is None:
        return PartnerRead(
            name=None,
            sex=None,
            avatar_config=None,
            game_age=GAME_AGE_DEFAULT,
            game_relation_happiness=GAME_RELATION_HAPPINESS_DEFAULT,
        )
    return _partner_read_from_player(partner_a)


def _partner_b_from_game(game: Game) -> PartnerRead | None:
    partner_b = _player_by_role(game, PlayerRole.PARTNER_B)
    if partner_b is None:
        return None
    return _partner_read_from_player(partner_b)


def _game_to_read(game: Game) -> GameRead:
    return GameRead(
        id=game.id,
        match_name=game.match_name,
        game_mode=game.game_mode,
        status=game.status,
        partner_a=_partner_a_from_game(game),
        partner_b=_partner_b_from_game(game),
    )


def _get_partner_a(game: Game) -> Player:
    partner_a = _player_by_role(game, PlayerRole.PARTNER_A)
    if partner_a is None:
        raise AppError(
            "INTERNAL_ERROR",
            _("Partner A not found for this game"),
            status_code=500,
        )
    return partner_a


def _ensure_partner_b(game: Game) -> Player:
    partner_b = _player_by_role(game, PlayerRole.PARTNER_B)
    if partner_b is not None:
        return partner_b
    partner_b = Player(
        role=PlayerRole.PARTNER_B.value,
        game_age=GAME_AGE_DEFAULT,
        game_relation_happiness=GAME_RELATION_HAPPINESS_DEFAULT,
    )
    game.players.append(partner_b)
    return partner_b


def _apply_avatar(player: Player, avatar_config: dict[str, Any]) -> None:
    validated = validate_avatar_config(avatar_config)
    if player.avatar_config is None:
        player.avatar_config = AvatarConfig(config=validated)
    else:
        player.avatar_config.config = validated


def _payload_has_partner_b_fields(payload: GameUpdate) -> bool:
    return any(
        value is not None
        for value in (
            payload.partner_b_name,
            payload.partner_b_sex,
            payload.partner_b_avatar_config,
            payload.partner_b_game_age,
            payload.partner_b_game_relation_happiness,
        )
    )


def _lobby_player_is_complete(player: Player) -> bool:
    has_name = player.name is not None and player.name.strip() != ""
    has_avatar = player.avatar_config is not None
    has_sex = player.sex is not None
    return has_name and has_avatar and has_sex


def _has_partner_b_run(game: Game) -> bool:
    return any(
        run.player_role == PlayerRole.PARTNER_B.value for run in game.simulation_runs
    )


def _apply_status(game: Game, partner_a: Player) -> None:
    if game.status == GameStatus.FINISHED.value:
        return
    if not _lobby_player_is_complete(partner_a):
        game.status = GameStatus.CREATED.value
        return
    if game.status == GameStatus.PLAYER_B_PLAYING.value or _has_partner_b_run(game):
        game.status = GameStatus.PLAYER_B_PLAYING.value
        return
    game.status = GameStatus.PLAYER_A_READY.value


def _load_game_with_players(db: Session, game_id: UUID) -> Game | None:
    return db.scalar(
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.players).selectinload(Player.avatar_config),
            selectinload(Game.simulation_runs),
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
    if not payload.model_dump(exclude_none=True):
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
        _apply_avatar(partner_a, payload.avatar_config)

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

    if _payload_has_partner_b_fields(payload):
        partner_b = _ensure_partner_b(game)
        if payload.partner_b_name is not None:
            partner_b.name = payload.partner_b_name
        if payload.partner_b_sex is not None:
            partner_b.sex = payload.partner_b_sex.value
        if payload.partner_b_avatar_config is not None:
            _apply_avatar(partner_b, payload.partner_b_avatar_config)
        if payload.partner_b_game_age is not None:
            partner_b.game_age = validate_game_age(
                payload.partner_b_game_age,
                field="body.partner_b_game_age",
            )
        if payload.partner_b_game_relation_happiness is not None:
            partner_b.game_relation_happiness = validate_game_relation_happiness(
                payload.partner_b_game_relation_happiness,
                field="body.partner_b_game_relation_happiness",
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
