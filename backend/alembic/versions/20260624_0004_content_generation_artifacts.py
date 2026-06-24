"""content generation artifacts

Revision ID: 20260624_0004
Revises: 20260511_0003
Create Date: 2026-06-24 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4
import hashlib
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "20260624_0004"
down_revision: Union[str, Sequence[str], None] = "20260511_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    task_columns = {column["name"] for column in inspector.get_columns("content_generation_task")}

    _add_task_columns(bind, task_columns)

    if not inspector.has_table("content_generation_artifact"):
        op.create_table(
            "content_generation_artifact",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("artifact_type", sa.String(length=32), nullable=False),
            sa.Column("unit_id", sa.String(length=128), nullable=True),
            sa.Column("unit_order", sa.Integer(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("schema_name", sa.String(length=128), nullable=True),
            sa.Column("schema_version", sa.String(length=32), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("payload_hash", sa.String(length=64), nullable=False),
            sa.Column("source_node", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_generation_artifact_task_id"), "content_generation_artifact", ["task_id"], unique=False)
        op.create_index(op.f("ix_content_generation_artifact_artifact_type"), "content_generation_artifact", ["artifact_type"], unique=False)
        op.create_index(op.f("ix_content_generation_artifact_unit_id"), "content_generation_artifact", ["unit_id"], unique=False)
        op.create_index(op.f("ix_content_generation_artifact_payload_hash"), "content_generation_artifact", ["payload_hash"], unique=False)

    if not inspector.has_table("content_generation_reference"):
        op.create_table(
            "content_generation_reference",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("artifact_id", sa.String(length=64), nullable=True),
            sa.Column("stage", sa.String(length=32), nullable=False),
            sa.Column("unit_id", sa.String(length=128), nullable=True),
            sa.Column("knowledge_base_id", sa.String(length=128), nullable=True),
            sa.Column("chunk_id", sa.String(length=255), nullable=False),
            sa.Column("source_id", sa.String(length=255), nullable=True),
            sa.Column("source_title", sa.String(length=512), nullable=True),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("retrieval_query", sa.Text(), nullable=True),
            sa.Column("content_excerpt", sa.Text(), nullable=True),
            sa.Column("content_hash", sa.String(length=64), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_generation_reference_task_id"), "content_generation_reference", ["task_id"], unique=False)
        op.create_index(op.f("ix_content_generation_reference_artifact_id"), "content_generation_reference", ["artifact_id"], unique=False)
        op.create_index(op.f("ix_content_generation_reference_stage"), "content_generation_reference", ["stage"], unique=False)
        op.create_index(op.f("ix_content_generation_reference_unit_id"), "content_generation_reference", ["unit_id"], unique=False)
        op.create_index(
            op.f("ix_content_generation_reference_knowledge_base_id"),
            "content_generation_reference",
            ["knowledge_base_id"],
            unique=False,
        )
        op.create_index(op.f("ix_content_generation_reference_chunk_id"), "content_generation_reference", ["chunk_id"], unique=False)
        op.create_index(op.f("ix_content_generation_reference_content_hash"), "content_generation_reference", ["content_hash"], unique=False)

    if not inspector.has_table("content_generation_asset"):
        op.create_table(
            "content_generation_asset",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("task_id", sa.String(length=64), nullable=False),
            sa.Column("unit_id", sa.String(length=128), nullable=True),
            sa.Column("asset_type", sa.String(length=32), nullable=False),
            sa.Column("provider", sa.String(length=64), nullable=True),
            sa.Column("model", sa.String(length=128), nullable=True),
            sa.Column("asset_url", sa.String(length=512), nullable=False),
            sa.Column("storage_key", sa.String(length=512), nullable=True),
            sa.Column("mime_type", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_content_generation_asset_task_id"), "content_generation_asset", ["task_id"], unique=False)
        op.create_index(op.f("ix_content_generation_asset_unit_id"), "content_generation_asset", ["unit_id"], unique=False)
        op.create_index(op.f("ix_content_generation_asset_asset_type"), "content_generation_asset", ["asset_type"], unique=False)
        op.create_index(op.f("ix_content_generation_asset_status"), "content_generation_asset", ["status"], unique=False)

    _migrate_existing_artifacts(bind)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_generation_asset_status"), table_name="content_generation_asset")
    op.drop_index(op.f("ix_content_generation_asset_asset_type"), table_name="content_generation_asset")
    op.drop_index(op.f("ix_content_generation_asset_unit_id"), table_name="content_generation_asset")
    op.drop_index(op.f("ix_content_generation_asset_task_id"), table_name="content_generation_asset")
    op.drop_table("content_generation_asset")

    op.drop_index(op.f("ix_content_generation_reference_content_hash"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_chunk_id"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_knowledge_base_id"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_unit_id"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_stage"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_artifact_id"), table_name="content_generation_reference")
    op.drop_index(op.f("ix_content_generation_reference_task_id"), table_name="content_generation_reference")
    op.drop_table("content_generation_reference")

    op.drop_index(op.f("ix_content_generation_artifact_payload_hash"), table_name="content_generation_artifact")
    op.drop_index(op.f("ix_content_generation_artifact_unit_id"), table_name="content_generation_artifact")
    op.drop_index(op.f("ix_content_generation_artifact_artifact_type"), table_name="content_generation_artifact")
    op.drop_index(op.f("ix_content_generation_artifact_task_id"), table_name="content_generation_artifact")
    op.drop_table("content_generation_artifact")

    for indexed_column in ["error_summary", "preview_url", "topic", "platform_session_id", "platform_user_id", "platform_log_id"]:
        op.drop_index(op.f(f"ix_content_generation_task_{indexed_column}"), table_name="content_generation_task")
    for column_name in ["error_summary", "preview_url", "generation_options", "topic", "platform_session_id", "platform_user_id", "platform_log_id"]:
        op.drop_column("content_generation_task", column_name)


def _add_task_columns(bind: object, columns: set[str]) -> None:
    text_defaults = {
        "platform_log_id": sa.Column("platform_log_id", sa.String(length=64), nullable=True),
        "platform_user_id": sa.Column("platform_user_id", sa.String(length=64), nullable=True),
        "platform_session_id": sa.Column("platform_session_id", sa.String(length=64), nullable=True),
        "topic": sa.Column("topic", sa.String(length=255), nullable=True),
        "preview_url": sa.Column("preview_url", sa.String(length=512), nullable=True),
        "error_summary": sa.Column("error_summary", sa.String(length=1000), nullable=True),
    }
    for name, column in text_defaults.items():
        if name not in columns:
            op.add_column("content_generation_task", column)
            op.create_index(op.f(f"ix_content_generation_task_{name}"), "content_generation_task", [name], unique=False)
    if "generation_options" not in columns:
        if bind.dialect.name == "sqlite":
            op.add_column("content_generation_task", sa.Column("generation_options", sa.JSON(), nullable=False, server_default="{}"))
        else:
            op.add_column("content_generation_task", sa.Column("generation_options", sa.JSON(), nullable=True))
            op.execute("UPDATE content_generation_task SET generation_options = '{}' WHERE generation_options IS NULL")
            op.alter_column("content_generation_task", "generation_options", existing_type=sa.JSON(), nullable=False)


def _migrate_existing_artifacts(bind: object) -> None:
    result = bind.execute(text("SELECT task_id, outline, content_spec, render_model, render_units, unit_results FROM content_generation_task"))
    rows = result.mappings().all()
    artifact_table = sa.table(
        "content_generation_artifact",
        sa.column("id", sa.String),
        sa.column("task_id", sa.String),
        sa.column("artifact_type", sa.String),
        sa.column("unit_id", sa.String),
        sa.column("unit_order", sa.Integer),
        sa.column("version", sa.Integer),
        sa.column("status", sa.String),
        sa.column("payload", sa.JSON),
        sa.column("payload_hash", sa.String),
        sa.column("source_node", sa.String),
    )
    payloads: list[dict[str, object]] = []
    for row in rows:
        task_id = row["task_id"]
        for artifact_type, column_name, source_node in [
            ("outline", "outline", "migration"),
            ("content_spec", "content_spec", "migration"),
            ("final_render", "render_model", "migration"),
        ]:
            payload = _json_payload(row[column_name])
            if payload:
                payloads.append(_artifact_row(task_id, artifact_type, payload, source_node=source_node))
        render_units = _json_payload(row["render_units"]) or {}
        if isinstance(render_units, dict):
            for unit_id, payload in render_units.items():
                if isinstance(payload, dict):
                    payloads.append(
                        _artifact_row(
                            task_id,
                            "unit_render",
                            payload,
                            unit_id=str(unit_id),
                            unit_order=payload.get("order") if isinstance(payload.get("order"), int) else None,
                            source_node="migration",
                        )
                    )
        unit_results = _json_payload(row["unit_results"]) or {}
        if isinstance(unit_results, dict):
            for unit_id, result in unit_results.items():
                unit_spec = result.get("unit_spec") if isinstance(result, dict) else None
                if isinstance(unit_spec, dict):
                    payloads.append(
                        _artifact_row(
                            task_id,
                            "unit_spec",
                            unit_spec,
                            unit_id=str(unit_id),
                            unit_order=unit_spec.get("order") if isinstance(unit_spec.get("order"), int) else None,
                            source_node="migration",
                        )
                    )
    if payloads:
        op.bulk_insert(artifact_table, payloads)


def _json_payload(value: object) -> object:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def _artifact_row(
    task_id: str,
    artifact_type: str,
    payload: dict[str, object],
    *,
    unit_id: str | None = None,
    unit_order: int | None = None,
    source_node: str | None = None,
) -> dict[str, object]:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "id": f"artifact_{uuid4().hex[:24]}",
        "task_id": task_id,
        "artifact_type": artifact_type,
        "unit_id": unit_id,
        "unit_order": unit_order,
        "version": 1,
        "status": "final",
        "payload": payload,
        "payload_hash": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "source_node": source_node,
    }
