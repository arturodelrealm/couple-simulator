import pytest

from app.shared.avatar_validation import validate_avatar_config
from app.shared.exceptions import AppError


def test_validate_avatar_config_accepts_allowed_variants():
    config = {
        "topVariant": "bigHair",
        "eyesVariant": "default",
        "accessoriesProbability": 50,
    }

    assert validate_avatar_config(config) == config


def test_validate_avatar_config_rejects_non_object():
    with pytest.raises(AppError) as exc_info:
        validate_avatar_config("not-a-dict")  # type: ignore[arg-type]

    assert exc_info.value.code == "INVALID_AVATAR_CONFIG"
    assert exc_info.value.status_code == 400
    assert exc_info.value.field == "body.avatar_config"


def test_validate_avatar_config_rejects_unknown_key():
    with pytest.raises(AppError) as exc_info:
        validate_avatar_config({"unknownOption": "value"})

    assert exc_info.value.code == "INVALID_AVATAR_CONFIG"
    assert "unknownOption" in exc_info.value.message


def test_validate_avatar_config_rejects_invalid_variant_value():
    with pytest.raises(AppError) as exc_info:
        validate_avatar_config({"topVariant": "not-a-real-hair-style"})

    assert exc_info.value.code == "INVALID_AVATAR_CONFIG"
    assert exc_info.value.field == "body.avatar_config.topVariant"


def test_validate_avatar_config_rejects_invalid_probability():
    with pytest.raises(AppError) as exc_info:
        validate_avatar_config({"accessoriesProbability": 101})

    assert exc_info.value.code == "INVALID_AVATAR_CONFIG"
    assert exc_info.value.field == "body.avatar_config.accessoriesProbability"


def test_validate_avatar_config_rejects_non_string_variant():
    with pytest.raises(AppError) as exc_info:
        validate_avatar_config({"eyesVariant": 123})

    assert exc_info.value.code == "INVALID_AVATAR_CONFIG"
    assert exc_info.value.field == "body.avatar_config.eyesVariant"
