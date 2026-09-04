from enum import Enum


class GameStatus(str, Enum):
    CREATED = "CREATED"
    PLAYER_A_READY = "PLAYER_A_READY"
    PLAYER_B_PLAYING = "PLAYER_B_PLAYING"
    FINISHED = "FINISHED"


class PlayerRole(str, Enum):
    PARTNER_A = "partner_a"
    PARTNER_B = "partner_b"


class GameMode(str, Enum):
    COUPLE = "couple"


class PlayerSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class SimulationRunStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


class SimulationRunKind(str, Enum):
    SIMULATION = "simulation"
    QUESTIONNAIRE = "questionnaire"
