"""content generation observability

Revision ID: 20260624_0005
Revises: 20260624_0004
Create Date: 2026-06-24 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260624_0005"
down_revision: Union[str, Sequence[str], None] = "20260624_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("content_generation_event"):
        op.create_table(
            "content_generation_event",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("node", sa.String(length=128), nullable=True),
            sa.Column("unit_id", sa.String(length=128), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_generation_event_task_id"), "content_generation_event", ["task_id"], unique=False)
        op.create_index(op.f("ix_content_generation_event_event_type"), "content_generation_event", ["event_type"], unique=False)
        op.create_index(op.f("ix_content_generation_event_node"), "content_generation_event", ["node"], unique=False)
        op.create_index(op.f("ix_content_generation_event_unit_id"), "content_generation_event", ["unit_id"], unique=False)
        op.create_index(op.f("ix_content_generation_event_created_at"), "content_generation_event", ["created_at"], unique=False)

    if not inspector.has_table("content_generation_metric"):
        op.create_table(
            "content_generation_metric",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("node", sa.String(length=128), nullable=False),
            sa.Column("unit_id", sa.String(length=128), nullable=True),
            sa.Column("provider", sa.String(length=64), nullable=True),
            sa.Column("model", sa.String(length=128), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("prompt_tokens", sa.Integer(), nullable=True),
            sa.Column("completion_tokens", sa.Integer(), nullable=True),
            sa.Column("total_tokens", sa.Integer(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("fallback_reason", sa.String(length=1000), nullable=True),
            sa.Column("error_type", sa.String(length=128), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_generation_metric_task_id"), "content_generation_metric", ["task_id"], unique=False)
        op.create_index(op.f("ix_content_generation_metric_node"), "content_generation_metric", ["node"], unique=False)
        op.create_index(op.f("ix_content_generation_metric_unit_id"), "content_generation_metric", ["unit_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_generation_metric_unit_id"), table_name="content_generation_metric")
    op.drop_index(op.f("ix_content_generation_metric_node"), table_name="content_generation_metric")
    op.drop_index(op.f("ix_content_generation_metric_task_id"), table_name="content_generation_metric")
    op.drop_table("content_generation_metric")

    op.drop_index(op.f("ix_content_generation_event_created_at"), table_name="content_generation_event")
    op.drop_index(op.f("ix_content_generation_event_unit_id"), table_name="content_generation_event")
    op.drop_index(op.f("ix_content_generation_event_node"), table_name="content_generation_event")
    op.drop_index(op.f("ix_content_generation_event_event_type"), table_name="content_generation_event")
    op.drop_index(op.f("ix_content_generation_event_task_id"), table_name="content_generation_event")
    op.drop_table("content_generation_event")
