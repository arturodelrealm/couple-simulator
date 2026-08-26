from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.enums import GameStatus

if TYPE_CHECKING:
    from app.models.player import Player


class Game(Base):
    __tablename__ = "games"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        String(32),
        default=GameStatus.CREATED.value,
        server_default=GameStatus.CREATED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    players: Mapped[list["Player"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
    )
