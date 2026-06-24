from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationArtifact(SQLModel, table=True):
    __tablename__ = "content_generation_artifact"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(index=True, max_length=64)
    artifact_type: str = Field(index=True, max_length=32)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    unit_order: int | None = Field(default=None)
    version: int = Field(default=1, nullable=False)
    status: str = Field(default="final", max_length=32)
    schema_name: str | None = Field(default=None, max_length=128)
    schema_version: str | None = Field(default=None, max_length=32)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    payload_hash: str = Field(index=True, max_length=64)
    source_node: str | None = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
