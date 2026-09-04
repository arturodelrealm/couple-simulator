"""Post-event passive income and household upkeep (no RNG)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import HousingQuality
from couple_simulator_engine.session import ClientAction, GameSession

INCOME_BAND_TAG = "income_band"
POST_EVENT_ECONOMY_ACTION = "post_event_economy"


def resolve_income_band(tags: Mapping[str, Any]) -> str | None:
    """Return a non-empty ``income_band`` string, or ``None`` if missing."""
    raw = tags.get(INCOME_BAND_TAG)
    if isinstance(raw, str) and raw:
        return raw
    return None


def resolve_passive_income(config: GameConfig, band: str | None) -> int:
    """Map a band to fixed income; missing/unknown bands use the default."""
    if band is None:
        return config.passive_income_default
    amount = config.passive_income_by_band.get(band)
    if amount is None:
        return config.passive_income_default
    return amount


def children_upkeep(config: GameConfig, children: int) -> int:
    """Upkeep magnitude once when the couple has at least one child."""
    if children >= 1:
        return config.passive_upkeep_children
    return 0


def housing_upkeep(config: GameConfig, quality: HousingQuality | str) -> int:
    """Upkeep magnitude when housing quality is excellent."""
    if quality == HousingQuality.EXCELLENT:
        return config.passive_upkeep_excellent_housing
    return 0


def compute_net_delta(income: int, upkeep_children: int, upkeep_housing: int) -> int:
    """Intended finances delta before clamp."""
    return income - upkeep_children - upkeep_housing


def apply_post_event_economy(
    session: GameSession, *, game_finished: bool
) -> list[ClientAction]:
    """Apply the tick and return ``post_event_economy`` or skip with no mutation."""
    if not session.config.passive_income_enabled or game_finished:
        return []
    config = session.config
    band = resolve_income_band(session.state.tags)
    income = resolve_passive_income(config, band)
    upkeep_children = children_upkeep(config, session.state.children)
    upkeep_housing = housing_upkeep(config, session.state.housing.quality)
    net = compute_net_delta(income, upkeep_children, upkeep_housing)
    session.state.set_stat("finances", session.state.finances + net)
    return [
        ClientAction(
            type=POST_EVENT_ECONOMY_ACTION,
            args={
                "income": income,
                "upkeep_children": upkeep_children,
                "upkeep_housing": upkeep_housing,
                "net": net,
                "income_band": band,
            },
        )
    ]
