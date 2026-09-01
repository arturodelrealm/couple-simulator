from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.simulation_run import SimulationRun


class TimelineEntry(Base):
    __tablename__ = "timeline_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    simulation_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64))
    age: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    simulation_run: Mapped["SimulationRun"] = relationship(
        back_populates="timeline_entries",
    )
