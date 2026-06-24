from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationReference(SQLModel, table=True):
    __tablename__ = "content_generation_reference"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(index=True, max_length=64)
    artifact_id: str | None = Field(default=None, index=True, max_length=64)
    stage: str = Field(index=True, max_length=32)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    knowledge_base_id: str | None = Field(default=None, index=True, max_length=128)
    chunk_id: str = Field(index=True, max_length=255)
    source_id: str | None = Field(default=None, max_length=255)
    source_title: str | None = Field(default=None, max_length=512)
    score: float | None = Field(default=None)
    retrieval_query: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    content_excerpt: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    content_hash: str | None = Field(default=None, index=True, max_length=64)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
