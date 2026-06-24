from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationMetric(SQLModel, table=True):
    __tablename__ = "content_generation_metric"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(index=True, max_length=64)
    node: str = Field(index=True, max_length=128)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    provider: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    duration_ms: int | None = Field(default=None)
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    retry_count: int = Field(default=0, nullable=False)
    fallback_used: bool = Field(default=False, nullable=False)
    fallback_reason: str | None = Field(default=None, max_length=1000)
    error_type: str | None = Field(default=None, max_length=128)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
