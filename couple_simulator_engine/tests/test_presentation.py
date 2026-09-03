"""Unit tests for TextPresentation and resolve_text_key."""

from couple_simulator_engine.content.definitions import TextPresentation
from couple_simulator_engine.content.presentation import resolve_text_key


def _full_presentation() -> TextPresentation:
    return TextPresentation(
        default_key="events.gift.question.default",
        by_role={
            "partner_a": "events.gift.question.role_a",
            "partner_b": "events.gift.question.role_b",
        },
        by_sex={
            "male": "events.gift.question.male",
            "female": "events.gift.question.female",
        },
    )


# --- Role precedence ---

def test_role_wins_over_sex_and_default() -> None:
    tp = _full_presentation()
    assert resolve_text_key(tp, player_role="partner_a", player_sex="female") == (
        "events.gift.question.role_a"
    )


def test_role_partner_b() -> None:
    tp = _full_presentation()
    assert resolve_text_key(tp, player_role="partner_b", player_sex="male") == (
        "events.gift.question.role_b"
    )


# --- Sex branch (no matching role) ---

def test_sex_male_when_role_absent() -> None:
    tp = TextPresentation(
        default_key="default",
        by_sex={"male": "key.male", "female": "key.female"},
    )
    assert resolve_text_key(tp, player_role="partner_a", player_sex="male") == (
        "key.male"
    )


def test_sex_female_when_role_absent() -> None:
    tp = TextPresentation(
        default_key="default",
        by_sex={"male": "key.male", "female": "key.female"},
    )
    assert resolve_text_key(tp, player_role="partner_a", player_sex="female") == (
        "key.female"
    )


# --- Other sex fallback ---

def test_other_sex_falls_back_to_default_when_absent() -> None:
    tp = TextPresentation(
        default_key="default.key",
        by_sex={"male": "key.male", "female": "key.female"},
    )
    assert resolve_text_key(tp, player_role="partner_a", player_sex="other") == (
        "default.key"
    )


def test_other_sex_uses_explicit_entry_when_present() -> None:
    tp = TextPresentation(
        default_key="default.key",
        by_sex={"male": "key.male", "female": "key.female", "other": "key.other"},
    )
    assert resolve_text_key(tp, player_role="partner_a", player_sex="other") == (
        "key.other"
    )


# --- Default-only presentation ---

def test_default_only_returns_default_key() -> None:
    tp = TextPresentation(default_key="events.simple.text")
    assert resolve_text_key(tp, player_role="partner_a", player_sex="male") == (
        "events.simple.text"
    )


# --- Plain string passthrough ---

def test_plain_string_returned_unchanged() -> None:
    assert resolve_text_key(
        "events.plain.key", player_role="partner_a", player_sex="male"
    ) == "events.plain.key"


# --- Unknown role falls through ---

def test_unknown_role_falls_to_sex() -> None:
    tp = TextPresentation(
        default_key="default",
        by_role={"partner_a": "role.a"},
        by_sex={"male": "sex.male"},
    )
    assert resolve_text_key(tp, player_role="partner_b", player_sex="male") == (
        "sex.male"
    )


def test_unknown_role_and_sex_falls_to_default() -> None:
    tp = TextPresentation(
        default_key="default",
        by_role={"partner_a": "role.a"},
        by_sex={"female": "sex.female"},
    )
    assert resolve_text_key(tp, player_role="partner_b", player_sex="other") == (
        "default"
    )
