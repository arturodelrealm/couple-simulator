from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.avatar_config import AvatarConfig
    from app.models.game import Game


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("game_id", "role", name="uq_players_game_id_role"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
    )
    role: Mapped[str] = mapped_column(String(32))
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    game: Mapped["Game"] = relationship(back_populates="players")
    avatar_config: Mapped[Optional["AvatarConfig"]] = relationship(
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )
