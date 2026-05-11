"""add task logs

Revision ID: 20260511_0002
Revises: 20260508_0001
Create Date: 2026-05-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0002"
down_revision: Union[str, Sequence[str], None] = "20260508_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.add_column("content_generation_task", sa.Column("logs", sa.JSON(), nullable=False, server_default="[]"))
        return
    op.add_column("content_generation_task", sa.Column("logs", sa.JSON(), nullable=True))
    op.execute("UPDATE content_generation_task SET logs = '[]' WHERE logs IS NULL")
    op.alter_column("content_generation_task", "logs", nullable=False)


def downgrade() -> None:
    op.drop_column("content_generation_task", "logs")
