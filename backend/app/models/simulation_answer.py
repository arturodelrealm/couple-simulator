from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.simulation_run import SimulationRun


class SimulationAnswer(Base):
    __tablename__ = "simulation_answers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    simulation_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        index=True,
    )
    event_id: Mapped[str] = mapped_column(String(255))
    question_id: Mapped[str] = mapped_column(String(255))
    option_id: Mapped[str] = mapped_column(String(255))
    sort_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    simulation_run: Mapped["SimulationRun"] = relationship(back_populates="answers")
