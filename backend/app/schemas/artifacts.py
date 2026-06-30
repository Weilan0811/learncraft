from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import SchemaModel


class ContentArtifactRecord(SchemaModel):
    id: str
    task_id: str
    artifact_type: str
    unit_id: str | None = None
    unit_order: int | None = None
    version: int = 1
    status: str = "final"
    schema_name: str | None = None
    schema_version: str | None = None
    payload: dict[str, Any]
    payload_hash: str = ""
    source_node: str | None = None
    created_at: datetime
    updated_at: datetime


class ContentReferenceRecord(SchemaModel):
    id: str
    task_id: str
    unit_id: str | None = None
    chunk_id: str
    source_path: str
    source_title: str | None = None
    rank: int | None = None
    score: float | None = None
    created_at: datetime


class ContentArtifactListResponse(SchemaModel):
    task_id: str
    artifacts: list[ContentArtifactRecord] = Field(default_factory=list)


class ContentArtifactDetailResponse(SchemaModel):
    task_id: str
    artifact: ContentArtifactRecord


class ContentReferenceListResponse(SchemaModel):
    task_id: str
    references: list[ContentReferenceRecord] = Field(default_factory=list)


class ReferenceChunk(SchemaModel):
    chunk_id: str
    path: str | None = None
    title: str
    text: str
    rank: int | None = None
    score: float | None = None


class ReferenceChunksResponse(SchemaModel):
    task_id: str
    unit_id: str | None = None
    content_type: str
    title: str | None = None
    chunks: list[ReferenceChunk] = Field(default_factory=list)


class GenerationMetricRecord(SchemaModel):
    id: str
    task_id: str
    node: str
    unit_id: str | None = None
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    error_type: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class GenerationMetricListResponse(SchemaModel):
    task_id: str
    metrics: list[GenerationMetricRecord] = Field(default_factory=list)
