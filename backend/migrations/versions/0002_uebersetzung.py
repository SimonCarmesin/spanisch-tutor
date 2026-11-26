"""Übersetzung von Nachrichten (FR-22)

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-26 16:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Beide Spalten sind optional: bestehende Zeilen bleiben gültig, kein Datenumbau nötig
    op.add_column("message", sa.Column("translation", sa.Text(), nullable=True))
    op.add_column("message", sa.Column("translation_keywords", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("message", "translation_keywords")
    op.drop_column("message", "translation")
