"""add content generation asset status fields

Revision ID: 20260701_0007
Revises: 20260630_0006
Create Date: 2026-07-01 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260701_0007"
down_revision: Union[str, Sequence[str], None] = "20260630_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_generation_asset",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="generated"),
    )
    op.add_column(
        "content_generation_asset",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_generation_asset",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "content_generation_asset",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_asset_status", "content_generation_asset", ["status"])
    op.execute("UPDATE content_generation_asset SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    op.drop_index("idx_asset_status", table_name="content_generation_asset")
    op.drop_column("content_generation_asset", "updated_at")
    op.drop_column("content_generation_asset", "retry_count")
    op.drop_column("content_generation_asset", "error_message")
    op.drop_column("content_generation_asset", "status")
