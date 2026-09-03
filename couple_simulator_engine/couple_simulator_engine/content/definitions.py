"""Immutable content types parsed from event JSON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from couple_simulator_engine.enums import LifeStage


@dataclass(frozen=True)
class ActionDefinition:
    type: str
    args: dict[str, Any]
    when: dict[str, Any] | None = None


@dataclass(frozen=True)
class TextPresentation:
    """Structured text field with optional role/sex variants (spec §6.2)."""

    default_key: str
    by_role: dict[str, str] | None = None
    by_sex: dict[str, str] | None = None


# Union accepted on question/option text after parsing.
TextField = str | TextPresentation


@dataclass(frozen=True)
class OptionDefinition:
    id: str
    text: TextField
    actions: tuple[ActionDefinition, ...] = ()


@dataclass(frozen=True)
class QuestionDefinition:
    id: str
    text: TextField
    options: tuple[OptionDefinition, ...]


@dataclass(frozen=True)
class OutcomeDefinition:
    id: str
    when: dict[str, Any] | None
    actions: tuple[ActionDefinition, ...]


@dataclass(frozen=True)
class EventDefinition:
    id: str
    title: str
    description: str | None
    tags: tuple[str, ...]
    life_stage: LifeStage | None
    eligibility: dict[str, Any] | None
    questions: tuple[QuestionDefinition, ...]
    outcomes: tuple[OutcomeDefinition, ...]
    default_actions: tuple[ActionDefinition, ...]
    mismatch_actions: tuple[ActionDefinition, ...]
    weight: float = 1.0
    max_occurrences: int = 1
