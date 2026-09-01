from app.shared.exceptions import AppError
from app.shared.i18n import translate as _

GAME_AGE_DEFAULT = 22
GAME_AGE_MIN = 18
GAME_RELATION_HAPPINESS_DEFAULT = 100
GAME_RELATION_HAPPINESS_MIN = 0
GAME_RELATION_HAPPINESS_MAX = 100


def validate_game_age(value: int, *, field: str) -> int:
    if value < GAME_AGE_MIN:
        raise AppError(
            "VALIDATION_ERROR",
            _("Game age must be at least %(min)s") % {"min": GAME_AGE_MIN},
            status_code=400,
            field=field,
        )
    return value


def validate_game_relation_happiness(value: int, *, field: str) -> int:
    if value < GAME_RELATION_HAPPINESS_MIN or value > GAME_RELATION_HAPPINESS_MAX:
        raise AppError(
            "VALIDATION_ERROR",
            _(
                "Relation happiness must be between %(min)s and %(max)s",
            )
            % {
                "min": GAME_RELATION_HAPPINESS_MIN,
                "max": GAME_RELATION_HAPPINESS_MAX,
            },
            status_code=400,
            field=field,
        )
    return value
