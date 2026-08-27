import json
from gettext import gettext as _
from pathlib import Path
from typing import Any

from app.shared.exceptions import AppError

_VARIANTS_PATH = Path(__file__).parent / "avataaars_variants.json"
_ALLOWED_VARIANTS: dict[str, list[str]] = json.loads(_VARIANTS_PATH.read_text())

_VARIANT_KEYS = frozenset(_ALLOWED_VARIANTS.keys())
_PROBABILITY_KEYS = frozenset({"accessoriesProbability", "facialHairProbability"})
_ALLOWED_KEYS = _VARIANT_KEYS | _PROBABILITY_KEYS


def validate_avatar_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise AppError(
            "INVALID_AVATAR_CONFIG",
            _("Avatar config must be an object"),
            status_code=400,
            field="body.avatar_config",
        )

    validated: dict[str, Any] = {}

    for key, value in config.items():
        if key not in _ALLOWED_KEYS:
            raise AppError(
                "INVALID_AVATAR_CONFIG",
                _("Unknown avatar option: %(key)s") % {"key": key},
                status_code=400,
                field="body.avatar_config",
            )

        if key in _PROBABILITY_KEYS:
            if not isinstance(value, int) or value < 0 or value > 100:
                raise AppError(
                    "INVALID_AVATAR_CONFIG",
                    _("Probability must be an integer between 0 and 100"),
                    status_code=400,
                    field=f"body.avatar_config.{key}",
                )
            validated[key] = value
            continue

        if not isinstance(value, str):
            raise AppError(
                "INVALID_AVATAR_CONFIG",
                _("Variant value must be a string"),
                status_code=400,
                field=f"body.avatar_config.{key}",
            )

        allowed = _ALLOWED_VARIANTS[key]
        if value not in allowed:
            raise AppError(
                "INVALID_AVATAR_CONFIG",
                _("Invalid value for %(key)s") % {"key": key},
                status_code=400,
                field=f"body.avatar_config.{key}",
            )
        validated[key] = value

    return validated


def get_allowed_variants() -> dict[str, list[str]]:
    return dict(_ALLOWED_VARIANTS)
