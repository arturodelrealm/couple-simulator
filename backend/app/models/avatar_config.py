from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.player import Player


class AvatarConfig(Base):
    __tablename__ = "avatar_configs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    player_id: Mapped[UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        unique=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSONB)

    player: Mapped["Player"] = relationship(back_populates="avatar_config")
