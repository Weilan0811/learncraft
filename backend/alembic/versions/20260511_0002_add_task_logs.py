"""add task logs

Revision ID: 20260511_0002
Revises: 20260508_0001
Create Date: 2026-05-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260511_0002"
down_revision: Union[str, Sequence[str], None] = "20260508_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("content_generation_task")}
    if "logs" in columns:
        return
    if bind.dialect.name == "sqlite":
        op.add_column("content_generation_task", sa.Column("logs", sa.JSON(), nullable=False, server_default="[]"))
        return
    op.add_column("content_generation_task", sa.Column("logs", sa.JSON(), nullable=True))
    op.execute("UPDATE content_generation_task SET logs = '[]' WHERE logs IS NULL")
    op.alter_column("content_generation_task", "logs", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    op.drop_column("content_generation_task", "logs")
