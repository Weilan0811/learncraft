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
    status: str
    schema_name: str | None = None
    schema_version: str | None = None
    payload: dict[str, Any]
    payload_hash: str
    source_node: str | None = None
    created_at: datetime
    updated_at: datetime


class ContentReferenceRecord(SchemaModel):
    id: str
    task_id: str
    artifact_id: str | None = None
    stage: str
    unit_id: str | None = None
    knowledge_base_id: str | None = None
    chunk_id: str
    source_id: str | None = None
    source_title: str | None = None
    score: float | None = None
    retrieval_query: str | None = None
    content_excerpt: str | None = None
    content_hash: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
