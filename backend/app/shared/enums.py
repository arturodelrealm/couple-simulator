from enum import Enum


class GameStatus(str, Enum):
    CREATED = "CREATED"
    PLAYER_A_READY = "PLAYER_A_READY"
    PLAYER_B_PLAYING = "PLAYER_B_PLAYING"
    FINISHED = "FINISHED"


class PlayerRole(str, Enum):
    PARTNER_A = "partner_a"
    PARTNER_B = "partner_b"
