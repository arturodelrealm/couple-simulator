"""In-memory catalog of loaded event definitions."""

from __future__ import annotations

from pathlib import Path

from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.content.loader import load_event_directory


class ContentCatalog:
    """Lookup table of events keyed by id."""

    def __init__(
        self, events: list[EventDefinition] | tuple[EventDefinition, ...] = ()
    ) -> None:
        self._events: dict[str, EventDefinition] = {event.id: event for event in events}

    def get(self, event_id: str) -> EventDefinition | None:
        return self._events.get(event_id)

    def all_events(self) -> tuple[EventDefinition, ...]:
        return tuple(self._events.values())


def load_catalog(path: str | Path) -> ContentCatalog:
    """Load every `*.json` event file from a directory into a catalog."""
    return ContentCatalog(load_event_directory(path))


def package_events_directory() -> Path:
    """Directory of packaged game events (`content/events/`)."""
    return Path(__file__).resolve().parent / "events"
