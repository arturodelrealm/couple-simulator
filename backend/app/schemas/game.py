from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums import GameMode, PlayerSex
from app.shared.match_name_validation import validate_match_name


class PartnerARead(BaseModel):
    name: str | None = None
    sex: str | None = None
    avatar_config: dict[str, Any] | None = None


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_name: str
    game_mode: str
    status: str
    partner_a: PartnerARead


class GameCreate(BaseModel):
    match_name: str
    game_mode: GameMode = GameMode.COUPLE
    partner_a_name: str | None = Field(default=None, min_length=1, max_length=255)
    partner_a_sex: PlayerSex | None = None
    avatar_config: dict[str, Any] | None = None

    @field_validator("match_name")
    @classmethod
    def validate_match_name_field(cls, value: str) -> str:
        return validate_match_name(value)

    @field_validator("partner_a_name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("partner_a_name must not be empty")
        return stripped


class GameUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    partner_a_name: str | None = Field(default=None, min_length=1, max_length=255)
    partner_a_sex: PlayerSex | None = None
    avatar_config: dict[str, Any] | None = None

    @field_validator("partner_a_name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("partner_a_name must not be empty")
        return stripped
