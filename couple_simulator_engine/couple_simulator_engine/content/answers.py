"""AnswerBank: Partner A recorded answers for exact event/question lookup."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.session import Answer, RecordedAnswer


@dataclass
class AnswerBank:
    """In-memory bank of recorded answers (V0: exact event_id + question_id)."""

    entries: list[RecordedAnswer] = field(default_factory=list)

    @classmethod
    def from_recorded_answers(cls, answers: Sequence[RecordedAnswer]) -> AnswerBank:
        return cls(entries=list(answers))

    def has_coverage_for(self, event_id: str) -> bool:
        return any(entry.event_id == event_id for entry in self.entries)

    def resolve_for_event(self, event: EventDefinition) -> list[Answer] | None:
        """Return answers for every event question, or None if any is missing.

        When several rows share the same ``(event_id, question_id)``, the last
        entry in ``entries`` wins.
        """
        option_by_question: dict[str, str] = {}
        for entry in self.entries:
            if entry.event_id == event.id:
                option_by_question[entry.question_id] = entry.option_id
        resolved: list[Answer] = []
        for question in event.questions:
            option_id = option_by_question.get(question.id)
            if option_id is None:
                return None
            resolved.append(Answer(question_id=question.id, option_id=option_id))
        return resolved
