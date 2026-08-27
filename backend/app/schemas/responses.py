from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ApiErrorEnvelope(BaseModel):
    errors: list[ApiErrorDetail]


class ApiSuccessEnvelope(BaseModel, Generic[T]):
    data: T


def ok(data: Any = None) -> dict[str, Any]:
    """Wrap a successful payload in the standard API envelope."""
    return {"data": data}
