"""Resolve TextPresentation to a single i18n key (spec §6.2)."""

from __future__ import annotations

from couple_simulator_engine.content.definitions import TextField


def resolve_text_key(
    text: TextField,
    *,
    player_role: str,
    player_sex: str,
) -> str:
    """Return the best i18n key for the active player context.

    Resolution order: ``by_role[player_role]`` → ``by_sex[player_sex]``
    → ``default_key``.  When *player_sex* is ``"other"`` and
    ``by_sex.other`` is absent, falls back to ``default_key``.
    """
    if isinstance(text, str):
        return text

    if text.by_role is not None:
        key = text.by_role.get(player_role)
        if key is not None:
            return key

    if text.by_sex is not None:
        key = text.by_sex.get(player_sex)
        if key is not None:
            return key

    return text.default_key
