"""Closed V0 enumerations for simulation state, players, and sessions."""

from enum import StrEnum


class LifeStage(StrEnum):
    YOUTH = "youth"
    ADULT = "adult"
    ELDERLY = "elderly"


class RelationshipStatus(StrEnum):
    TOGETHER = "together"
    SEPARATED = "separated"
    WIDOWED = "widowed"


class PlayerSex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
