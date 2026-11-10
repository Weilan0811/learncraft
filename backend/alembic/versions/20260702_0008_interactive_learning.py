"""add interactive learning sessions and events

Revision ID: 20260702_0008
Revises: 20260701_0007
Create Date: 2026-07-02 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260702_0008"
down_revision: Union[str, Sequence[str], None] = "20260701_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if not _has_table("interactive_learning_session"):
        op.create_table(
            "interactive_learning_session",
            sa.Column("session_id", sa.String(length=64), primary_key=True),
            sa.Column("lesson_id", sa.String(length=128), nullable=False),
            sa.Column("state", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
    if not _has_index("interactive_learning_session", "ix_interactive_learning_session_lesson_id"):
        op.create_index(
            "ix_interactive_learning_session_lesson_id",
            "interactive_learning_session",
            ["lesson_id"],
        )

    if not _has_table("interactive_learning_event"):
        op.create_table(
            "interactive_learning_event",
            sa.Column("event_id", sa.String(length=64), primary_key=True),
            sa.Column("session_id", sa.String(length=64), nullable=False),
            sa.Column("lesson_id", sa.String(length=128), nullable=False),
            sa.Column("section_id", sa.String(length=128), nullable=False),
            sa.Column("block_id", sa.String(length=128), nullable=True),
            sa.Column("interaction_id", sa.String(length=128), nullable=True),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["session_id"],
                ["interactive_learning_session.session_id"],
            ),
        )
    for index_name, columns in (
        ("ix_interactive_learning_event_session_id", ["session_id"]),
        ("ix_interactive_learning_event_lesson_id", ["lesson_id"]),
        ("ix_interactive_learning_event_section_id", ["section_id"]),
        ("ix_interactive_learning_event_event_type", ["event_type"]),
    ):
        if not _has_index("interactive_learning_event", index_name):
            op.create_index(index_name, "interactive_learning_event", columns)


def downgrade() -> None:
    if _has_table("interactive_learning_event"):
        op.drop_table("interactive_learning_event")
    if _has_table("interactive_learning_session"):
        op.drop_table("interactive_learning_session")
