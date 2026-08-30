"""Session-level configuration for V0."""

from dataclasses import dataclass


@dataclass
class GameConfig:
    max_events: int = 5
