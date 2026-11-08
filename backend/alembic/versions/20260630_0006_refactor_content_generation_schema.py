"""refactor content generation schema

Revision ID: 20260630_0006
Revises: 20260624_0005
Create Date: 2026-06-30 00:00:00.000000

"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "20260630_0006"
down_revision: Union[str, Sequence[str], None] = "20260624_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _drop_if_exists(inspector, "content_generation_event")
    _drop_if_exists(inspector, "content_generation_metric")

    legacy_names: dict[str, str] = {}
    for table_name in [
        "content_generation_reference",
        "content_generation_asset",
        "content_generation_artifact",
        "content_generation_task",
    ]:
        if inspect(bind).has_table(table_name):
            legacy_name = f"{table_name}_legacy_0006"
            _drop_if_exists(inspect(bind), legacy_name)
            op.rename_table(table_name, legacy_name)
            legacy_names[table_name] = legacy_name

    _create_new_tables()
    _copy_tasks(bind, legacy_names.get("content_generation_task"))
    _copy_artifacts(bind, legacy_names.get("content_generation_artifact"), legacy_names.get("content_generation_task"))
    _copy_references(bind, legacy_names.get("content_generation_reference"))
    _copy_assets(bind, legacy_names.get("content_generation_asset"))

    for legacy_name in legacy_names.values():
        _drop_if_exists(inspect(bind), legacy_name)


def downgrade() -> None:
    op.drop_table("content_generation_asset")
    op.drop_table("content_generation_reference")
    op.drop_table("knowledge_chunk_cache")
    op.drop_table("content_generation_artifact")
    op.drop_table("content_generation_task")


def _create_new_tables() -> None:
    op.create_table(
        "content_generation_task",
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("platform_log_id", sa.String(length=64), nullable=True),
        sa.Column("platform_user_id", sa.String(length=64), nullable=True),
        sa.Column("platform_session_id", sa.String(length=64), nullable=True),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.JSON(), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_index("idx_task_platform_log_id", "content_generation_task", ["platform_log_id"])
    op.create_index("idx_task_platform_user_id", "content_generation_task", ["platform_user_id"])
    op.create_index("idx_task_platform_session_id", "content_generation_task", ["platform_session_id"])
    op.create_index("idx_task_content_type", "content_generation_task", ["content_type"])
    op.create_index("idx_task_status", "content_generation_task", ["status"])

    op.create_table(
        "content_generation_artifact",
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("unit_id", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["content_generation_task.task_id"]),
        sa.PrimaryKeyConstraint("artifact_id"),
    )
    op.create_index("idx_artifact_task_id", "content_generation_artifact", ["task_id"])
    op.create_index("idx_artifact_task_type", "content_generation_artifact", ["task_id", "artifact_type"])
    op.create_index("idx_artifact_task_unit", "content_generation_artifact", ["task_id", "unit_id"])
    op.create_index("idx_artifact_task_type_unit", "content_generation_artifact", ["task_id", "artifact_type", "unit_id"])

    op.create_table(
        "knowledge_chunk_cache",
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text().with_variant(sa.dialects.mysql.LONGTEXT(), "mysql"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("chunk_id"),
    )

    op.create_table(
        "content_generation_reference",
        sa.Column("reference_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("unit_id", sa.String(length=128), nullable=True),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["knowledge_chunk_cache.chunk_id"]),
        sa.ForeignKeyConstraint(["task_id"], ["content_generation_task.task_id"]),
        sa.PrimaryKeyConstraint("reference_id"),
        sa.UniqueConstraint("task_id", "unit_id", "chunk_id", "source_path", name="uq_reference_dedup"),
    )
    op.create_index("idx_reference_task_id", "content_generation_reference", ["task_id"])
    op.create_index("idx_reference_task_unit", "content_generation_reference", ["task_id", "unit_id"])
    op.create_index("idx_reference_chunk_id", "content_generation_reference", ["chunk_id"])

    op.create_table(
        "content_generation_asset",
        sa.Column("asset_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("unit_id", sa.String(length=128), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("uri", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["content_generation_task.task_id"]),
        sa.PrimaryKeyConstraint("asset_id"),
    )
    op.create_index("idx_asset_task_id", "content_generation_asset", ["task_id"])
    op.create_index("idx_asset_task_unit", "content_generation_asset", ["task_id", "unit_id"])
    op.create_index("idx_asset_type", "content_generation_asset", ["asset_type"])


def _copy_tasks(bind: sa.Connection, legacy_table: str | None) -> None:
    if not legacy_table:
        return
    rows = bind.execute(text(f"SELECT * FROM {legacy_table}")).mappings().all()
    for row in rows:
        request_payload = _json(row.get("request_payload")) or {}
        error_message = row.get("error_message") or row.get("error_summary")
        errors = _json(row.get("errors")) or []
        if not error_message and isinstance(errors, list) and errors:
            error_message = str(errors[-1])
        bind.execute(
            text(
                """
                INSERT INTO content_generation_task (
                    task_id, platform_log_id, platform_user_id, platform_session_id,
                    content_type, topic, status, progress, request_payload, error_message,
                    created_at, updated_at, started_at, completed_at
                ) VALUES (
                    :task_id, :platform_log_id, :platform_user_id, :platform_session_id,
                    :content_type, :topic, :status, :progress, :request_payload, :error_message,
                    :created_at, :updated_at, :started_at, :completed_at
                )
                """
            ),
            {
                "task_id": row["task_id"],
                "platform_log_id": row.get("platform_log_id"),
                "platform_user_id": row.get("platform_user_id"),
                "platform_session_id": row.get("platform_session_id"),
                "content_type": row["content_type"],
                "topic": row.get("topic") or request_payload.get("topic"),
                "status": row["status"],
                "progress": _dump(_json(row.get("progress")) or {}),
                "request_payload": _dump(request_payload),
                "error_message": error_message,
                "created_at": row.get("created_at") or _now(),
                "updated_at": row.get("updated_at") or _now(),
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
            },
        )


def _copy_artifacts(bind: sa.Connection, legacy_artifact: str | None, legacy_task: str | None) -> None:
    seen: set[tuple[str, str, str | None]] = set()
    if legacy_artifact:
        rows = bind.execute(text(f"SELECT * FROM {legacy_artifact}")).mappings().all()
        for row in rows:
            payload = _json(row.get("payload")) or {}
            key = (row["task_id"], row["artifact_type"], row.get("unit_id"))
            seen.add(key)
            _insert_artifact(
                bind,
                artifact_id=row.get("artifact_id") or row.get("id") or _new_id("artifact"),
                task_id=row["task_id"],
                artifact_type=row["artifact_type"],
                unit_id=row.get("unit_id"),
                version=int(row.get("version") or 1),
                payload=payload,
                created_at=row.get("created_at") or _now(),
                updated_at=row.get("updated_at") or _now(),
            )
    if not legacy_task:
        return
    rows = bind.execute(text(f"SELECT * FROM {legacy_task}")).mappings().all()
    for row in rows:
        task_id = row["task_id"]
        for artifact_type, column_name in [
            ("outline", "outline"),
            ("content_spec", "content_spec"),
            ("partial_render", "partial_render_model"),
            ("final_render", "render_model"),
        ]:
            payload = _json(row.get(column_name))
            if not payload or (task_id, artifact_type, None) in seen:
                continue
            if artifact_type == "final_render":
                payload = {"content_type": row["content_type"], "render_model": payload}
            _insert_artifact(bind, _new_id("artifact"), task_id, artifact_type, None, 1, payload, row.get("created_at"), row.get("updated_at"))
        render_units = _json(row.get("render_units")) or {}
        if isinstance(render_units, dict):
            for unit_id, payload in render_units.items():
                if isinstance(payload, dict) and (task_id, "unit_render", str(unit_id)) not in seen:
                    _insert_artifact(bind, _new_id("artifact"), task_id, "unit_render", str(unit_id), 1, payload, row.get("created_at"), row.get("updated_at"))


def _copy_references(bind: sa.Connection, legacy_table: str | None) -> None:
    if not legacy_table:
        return
    rows = bind.execute(text(f"SELECT * FROM {legacy_table}")).mappings().all()
    for index, row in enumerate(rows, start=1):
        text_value = str(row.get("content_excerpt") or "").strip()
        if not text_value:
            continue
        normalized = _normalize(text_value)
        chunk_id = _chunk_id(normalized)
        now = row.get("created_at") or _now()
        source_path = _source_path(row)
        reference_id = row.get("reference_id") or row.get("id") or _reference_id(row["task_id"], row.get("unit_id"), chunk_id, source_path)
        bind.execute(
            text(
                f"""
                {_insert_ignore_prefix(bind)} INTO knowledge_chunk_cache (chunk_id, text, created_at, last_seen_at)
                VALUES (:chunk_id, :text, :created_at, :last_seen_at)
                """
            ),
            {"chunk_id": chunk_id, "text": normalized, "created_at": now, "last_seen_at": now},
        )
        bind.execute(
            text(
                f"""
                {_insert_ignore_prefix(bind)} INTO content_generation_reference (
                    reference_id, task_id, unit_id, chunk_id, source_path, source_title, rank, score, created_at
                ) VALUES (
                    :reference_id, :task_id, :unit_id, :chunk_id, :source_path, :source_title, :rank, :score, :created_at
                )
                """
            ),
            {
                "reference_id": reference_id,
                "task_id": row["task_id"],
                "unit_id": row.get("unit_id"),
                "chunk_id": chunk_id,
                "source_path": source_path,
                "source_title": row.get("source_title"),
                "rank": index,
                "score": row.get("score"),
                "created_at": now,
            },
        )


def _copy_assets(bind: sa.Connection, legacy_table: str | None) -> None:
    if not legacy_table:
        return
    rows = bind.execute(text(f"SELECT * FROM {legacy_table}")).mappings().all()
    for row in rows:
        metadata = _json(row.get("metadata")) or {}
        for key in ["provider", "model", "storage_key", "status"]:
            if row.get(key) is not None:
                metadata[key] = row.get(key)
        bind.execute(
            text(
                """
                INSERT INTO content_generation_asset (
                    asset_id, task_id, unit_id, asset_type, uri, mime_type, metadata, created_at
                ) VALUES (
                    :asset_id, :task_id, :unit_id, :asset_type, :uri, :mime_type, :metadata, :created_at
                )
                """
            ),
            {
                "asset_id": row.get("asset_id") or row.get("id") or _new_id("asset"),
                "task_id": row["task_id"],
                "unit_id": row.get("unit_id"),
                "asset_type": row["asset_type"],
                "uri": row.get("uri") or row.get("asset_url"),
                "mime_type": row.get("mime_type"),
                "metadata": _dump(metadata),
                "created_at": row.get("created_at") or _now(),
            },
        )


def _insert_artifact(
    bind: sa.Connection,
    artifact_id: str,
    task_id: str,
    artifact_type: str,
    unit_id: str | None,
    version: int,
    payload: dict,
    created_at: object,
    updated_at: object,
) -> None:
    bind.execute(
        text(
            """
            INSERT INTO content_generation_artifact (
                artifact_id, task_id, artifact_type, unit_id, version, payload, created_at, updated_at
            ) VALUES (
                :artifact_id, :task_id, :artifact_type, :unit_id, :version, :payload, :created_at, :updated_at
            )
            """
        ),
        {
            "artifact_id": artifact_id,
            "task_id": task_id,
            "artifact_type": artifact_type,
            "unit_id": unit_id,
            "version": version,
            "payload": _dump(payload),
            "created_at": created_at or _now(),
            "updated_at": updated_at or _now(),
        },
    )


def _drop_if_exists(inspector: sa.Inspector, table_name: str) -> None:
    if inspector.has_table(table_name):
        op.drop_table(table_name)


def _insert_ignore_prefix(bind: sa.Connection) -> str:
    if bind.dialect.name == "sqlite":
        return "INSERT OR IGNORE"
    if bind.dialect.name == "mysql":
        return "INSERT IGNORE"
    return "INSERT"


def _json(value: object) -> object:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize(value: str) -> str:
    return value.strip().replace("\r\n", "\n")


def _chunk_id(value: str) -> str:
    return hashlib.sha256(_normalize(value).encode("utf-8")).hexdigest()


def _reference_id(task_id: str, unit_id: str | None, chunk_id: str, source_path: str) -> str:
    return hashlib.sha256("|".join([task_id, unit_id or "", chunk_id, source_path]).encode("utf-8")).hexdigest()


def _source_path(row: sa.RowMapping) -> str:
    metadata = _json(row.get("metadata")) or {}
    if isinstance(metadata, dict) and isinstance(metadata.get("path"), str) and metadata["path"]:
        return metadata["path"]
    return str(row.get("source_id") or row.get("chunk_id") or "unknown")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:24]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)
