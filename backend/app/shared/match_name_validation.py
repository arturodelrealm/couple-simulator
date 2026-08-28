import re
from gettext import gettext as _

from app.shared.exceptions import AppError

_MATCH_NAME_PATTERN = re.compile(r"^[a-z0-9_-]{3,32}$")


def normalize_match_name(value: str) -> str:
    return value.strip().lower()


def validate_match_name(value: str, *, field: str = "body.match_name") -> str:
    normalized = normalize_match_name(value)
    if not _MATCH_NAME_PATTERN.match(normalized):
        raise AppError(
            "VALIDATION_ERROR",
            _("Invalid match name format"),
            status_code=422,
            field=field,
        )
    return normalized
