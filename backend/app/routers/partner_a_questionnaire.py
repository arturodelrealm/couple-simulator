from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.partner_a_questionnaire import (
    QuestionnaireEventUpdateRead,
    QuestionnaireRead,
)
from app.schemas.responses import ok
from app.schemas.simulation import EventAnswersSubmit
from app.services import partner_a_questionnaire as questionnaire_service

router = APIRouter()


@router.get("/{game_id}/partner-a/questionnaire")
def get_partner_a_questionnaire(
    game_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    payload = questionnaire_service.get_questionnaire(db, game_id)
    return ok(QuestionnaireRead.model_validate(payload).model_dump())


@router.put("/{game_id}/partner-a/questionnaire/events/{event_id}/answers")
def put_partner_a_questionnaire_answers(
    game_id: UUID,
    event_id: str,
    payload: EventAnswersSubmit,
    db: Session = Depends(get_db),
) -> dict:
    result = questionnaire_service.save_event_answers(
        db,
        game_id,
        event_id,
        answers=[item.model_dump() for item in payload.answers],
    )
    return ok(QuestionnaireEventUpdateRead.model_validate(result).model_dump())


@router.post("/{game_id}/partner-a/questionnaire/events/{event_id}/skip")
def post_partner_a_questionnaire_skip(
    game_id: UUID,
    event_id: str,
    db: Session = Depends(get_db),
) -> dict:
    result = questionnaire_service.skip_event(db, game_id, event_id)
    return ok(QuestionnaireEventUpdateRead.model_validate(result).model_dump())


@router.post("/{game_id}/partner-a/questionnaire/events/{event_id}/unskip")
def post_partner_a_questionnaire_unskip(
    game_id: UUID,
    event_id: str,
    db: Session = Depends(get_db),
) -> dict:
    result = questionnaire_service.unskip_event(db, game_id, event_id)
    return ok(QuestionnaireEventUpdateRead.model_validate(result).model_dump())
