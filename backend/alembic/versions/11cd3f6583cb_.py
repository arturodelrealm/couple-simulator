"""add match_name game_mode and player sex

Revision ID: 11cd3f6583cb
Revises: 001_initial_mvp0
Create Date: 2026-08-28 23:32:20.233237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11cd3f6583cb'
down_revision: Union[str, Sequence[str], None] = '001_initial_mvp0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dev/staging: existing MVP0 games have no match_name; wipe before NOT NULL column.
    op.execute("DELETE FROM games")

    op.add_column("games", sa.Column("match_name", sa.String(length=32), nullable=False))
    op.add_column(
        "games",
        sa.Column("game_mode", sa.String(length=32), server_default="couple", nullable=False),
    )
    op.create_index(op.f("ix_games_match_name"), "games", ["match_name"], unique=True)
    op.add_column("players", sa.Column("sex", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "sex")
    op.drop_index(op.f("ix_games_match_name"), table_name="games")
    op.drop_column("games", "game_mode")
    op.drop_column("games", "match_name")
