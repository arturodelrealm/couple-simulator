from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PartnerARead(BaseModel):
    name: str | None = None
    avatar_config: dict[str, Any] | None = None


class GameRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    partner_a: PartnerARead


class GameCreate(BaseModel):
    partner_a_name: str = Field(min_length=1, max_length=255)

    @field_validator("partner_a_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("partner_a_name must not be empty")
        return stripped


class GameUpdate(BaseModel):
    partner_a_name: str | None = Field(default=None, min_length=1, max_length=255)
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
