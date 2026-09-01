from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.enums import SimulationRunStatus

if TYPE_CHECKING:
    from app.models.game import Game
    from app.models.simulation_answer import SimulationAnswer
    from app.models.timeline_entry import TimelineEntry


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    __table_args__ = (
        Index("ix_simulation_runs_game_id_player_role", "game_id", "player_role"),
        Index("ix_simulation_runs_game_id_status", "game_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        index=True,
    )
    player_role: Mapped[str] = mapped_column(String(32))
    run_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(32),
        default=SimulationRunStatus.ACTIVE.value,
        server_default=SimulationRunStatus.ACTIVE.value,
    )
    rng_seed: Mapped[int] = mapped_column(Integer)
    events_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )
    events_played_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    current_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    event_variables: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    max_events: Mapped[int] = mapped_column(Integer)
    end_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    game: Mapped["Game"] = relationship(back_populates="simulation_runs")
    answers: Mapped[list["SimulationAnswer"]] = relationship(
        back_populates="simulation_run",
        cascade="all, delete-orphan",
    )
    timeline_entries: Mapped[list["TimelineEntry"]] = relationship(
        back_populates="simulation_run",
        cascade="all, delete-orphan",
    )
