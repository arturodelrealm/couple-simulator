from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.game import GameCreate, GameUpdate
from app.schemas.responses import ok
from app.services import game_service

router = APIRouter()


@router.post("", status_code=201)
def create_game(
    payload: GameCreate,
    db: Session = Depends(get_db),
) -> dict:
    game = game_service.create_game(db, payload)
    return ok(game.model_dump())


@router.get("/by-match-name/{match_name}")
def get_game_by_match_name(
    match_name: str,
    db: Session = Depends(get_db),
) -> dict:
    game = game_service.get_game_by_match_name(db, match_name)
    return ok(game.model_dump())


@router.get("/{game_id}")
def get_game(
    game_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    game = game_service.get_game(db, game_id)
    return ok(game.model_dump())


@router.patch("/{game_id}")
def update_game(
    game_id: UUID,
    payload: GameUpdate,
    db: Session = Depends(get_db),
) -> dict:
    game = game_service.update_game(db, game_id, payload)
    return ok(game.model_dump())
