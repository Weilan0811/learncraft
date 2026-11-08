from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ContentGenerationTask(SQLModel, table=True):
    __tablename__ = "content_generation_task"

    task_id: str = Field(primary_key=True, max_length=64)
    platform_log_id: str | None = Field(default=None, index=True, max_length=64)
    platform_user_id: str | None = Field(default=None, index=True, max_length=64)
    platform_session_id: str | None = Field(default=None, index=True, max_length=64)
    content_type: str = Field(index=True, max_length=32)
    topic: str | None = Field(default=None, max_length=255)
    status: str = Field(index=True, max_length=32)
    progress: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))
    request_payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
