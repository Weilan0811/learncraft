"""create_content_generation_task

Revision ID: 20260508_0001
Revises:
Create Date: 2026-05-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_generation_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_node", sa.String(length=128), nullable=True),
        sa.Column("progress", sa.JSON(), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("render_model", sa.JSON(), nullable=True),
        sa.Column("content_spec", sa.JSON(), nullable=True),
        sa.Column("elements", sa.JSON(), nullable=False),
        sa.Column("asset_ids", sa.JSON(), nullable=False),
        sa.Column("export_files", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_generation_task_content_type"), "content_generation_task", ["content_type"], unique=False)
    op.create_index(op.f("ix_content_generation_task_status"), "content_generation_task", ["status"], unique=False)
    op.create_index(op.f("ix_content_generation_task_task_id"), "content_generation_task", ["task_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_generation_task_task_id"), table_name="content_generation_task")
    op.drop_index(op.f("ix_content_generation_task_status"), table_name="content_generation_task")
    op.drop_index(op.f("ix_content_generation_task_content_type"), table_name="content_generation_task")
    op.drop_table("content_generation_task")
