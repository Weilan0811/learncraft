"""add streaming snapshots

Revision ID: 20260511_0003
Revises: 20260511_0002
Create Date: 2026-05-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260511_0003"
down_revision: Union[str, Sequence[str], None] = "20260511_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("content_generation_task")}

    if "outline" not in columns:
        op.add_column("content_generation_task", sa.Column("outline", sa.JSON(), nullable=True))
    if "partial_render_model" not in columns:
        op.add_column("content_generation_task", sa.Column("partial_render_model", sa.JSON(), nullable=True))

    if bind.dialect.name == "sqlite":
        if "unit_results" not in columns:
            op.add_column("content_generation_task", sa.Column("unit_results", sa.JSON(), nullable=False, server_default="{}"))
        if "render_units" not in columns:
            op.add_column("content_generation_task", sa.Column("render_units", sa.JSON(), nullable=False, server_default="{}"))
        if "stream_events" not in columns:
            op.add_column("content_generation_task", sa.Column("stream_events", sa.JSON(), nullable=False, server_default="[]"))
        return

    if "unit_results" not in columns:
        op.add_column("content_generation_task", sa.Column("unit_results", sa.JSON(), nullable=True))
        op.execute("UPDATE content_generation_task SET unit_results = '{}' WHERE unit_results IS NULL")
        op.alter_column("content_generation_task", "unit_results", existing_type=sa.JSON(), nullable=False)
    if "render_units" not in columns:
        op.add_column("content_generation_task", sa.Column("render_units", sa.JSON(), nullable=True))
        op.execute("UPDATE content_generation_task SET render_units = '{}' WHERE render_units IS NULL")
        op.alter_column("content_generation_task", "render_units", existing_type=sa.JSON(), nullable=False)
    if "stream_events" not in columns:
        op.add_column("content_generation_task", sa.Column("stream_events", sa.JSON(), nullable=True))
        op.execute("UPDATE content_generation_task SET stream_events = '[]' WHERE stream_events IS NULL")
        op.alter_column("content_generation_task", "stream_events", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    op.drop_column("content_generation_task", "stream_events")
    op.drop_column("content_generation_task", "render_units")
    op.drop_column("content_generation_task", "unit_results")
    op.drop_column("content_generation_task", "partial_render_model")
    op.drop_column("content_generation_task", "outline")
