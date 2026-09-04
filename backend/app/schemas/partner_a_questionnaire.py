from typing import Literal

from pydantic import BaseModel

from app.schemas.simulation import EventAnswerItem, EventPresentationRead

QuestionnaireItemStatus = Literal["pending", "answered", "skipped"]


class QuestionnaireProgressRead(BaseModel):
    answered: int
    skipped: int
    total: int
    complete: bool


class QuestionnaireAvatarPreviewRead(BaseModel):
    question_id: str
    option_id: str
    player: str
    attribute: str
    value: str | int


class QuestionnaireItemRead(BaseModel):
    event_id: str
    presentation: EventPresentationRead
    status: QuestionnaireItemStatus
    saved_answers: list[EventAnswerItem]
    avatar_previews: list[QuestionnaireAvatarPreviewRead] = []


class QuestionnaireRead(BaseModel):
    items: list[QuestionnaireItemRead]
    progress: QuestionnaireProgressRead


class QuestionnaireEventUpdateRead(BaseModel):
    item: QuestionnaireItemRead
    progress: QuestionnaireProgressRead
