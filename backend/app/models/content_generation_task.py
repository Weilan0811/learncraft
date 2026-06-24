from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ContentGenerationTask(SQLModel, table=True):
    __tablename__ = "content_generation_task"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True, max_length=64)
    platform_log_id: str | None = Field(default=None, index=True, max_length=64)
    platform_user_id: str | None = Field(default=None, index=True, max_length=64)
    platform_session_id: str | None = Field(default=None, index=True, max_length=64)
    content_type: str = Field(index=True, max_length=32)
    topic: str | None = Field(default=None, max_length=255)
    status: str = Field(index=True, max_length=32)
    current_node: str | None = Field(default=None, max_length=128)
    progress: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    request_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    generation_options: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    preview_url: str | None = Field(default=None, max_length=512)
    error_summary: str | None = Field(default=None, max_length=1000)
    outline: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    render_model: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    partial_render_model: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    content_spec: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    unit_results: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    render_units: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    stream_events: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    elements: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    logs: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    asset_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    export_files: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    errors: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
