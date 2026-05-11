"""add streaming snapshots

Revision ID: 20260511_0003
Revises: 20260511_0002
Create Date: 2026-05-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260511_0003"
down_revision: Union[str, Sequence[str], None] = "20260511_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_generation_task", sa.Column("outline", sa.JSON(), nullable=True))
    op.add_column("content_generation_task", sa.Column("partial_render_model", sa.JSON(), nullable=True))
    if op.get_bind().dialect.name == "sqlite":
        op.add_column("content_generation_task", sa.Column("unit_results", sa.JSON(), nullable=False, server_default="{}"))
        op.add_column("content_generation_task", sa.Column("render_units", sa.JSON(), nullable=False, server_default="{}"))
        op.add_column("content_generation_task", sa.Column("stream_events", sa.JSON(), nullable=False, server_default="[]"))
        return
    op.add_column("content_generation_task", sa.Column("unit_results", sa.JSON(), nullable=True))
    op.add_column("content_generation_task", sa.Column("render_units", sa.JSON(), nullable=True))
    op.add_column("content_generation_task", sa.Column("stream_events", sa.JSON(), nullable=True))
    op.execute("UPDATE content_generation_task SET unit_results = '{}' WHERE unit_results IS NULL")
    op.execute("UPDATE content_generation_task SET render_units = '{}' WHERE render_units IS NULL")
    op.execute("UPDATE content_generation_task SET stream_events = '[]' WHERE stream_events IS NULL")
    op.alter_column("content_generation_task", "unit_results", nullable=False)
    op.alter_column("content_generation_task", "render_units", nullable=False)
    op.alter_column("content_generation_task", "stream_events", nullable=False)


def downgrade() -> None:
    op.drop_column("content_generation_task", "stream_events")
    op.drop_column("content_generation_task", "render_units")
    op.drop_column("content_generation_task", "unit_results")
    op.drop_column("content_generation_task", "partial_render_model")
    op.drop_column("content_generation_task", "outline")
