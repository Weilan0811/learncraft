from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


class BaseElement(SchemaModel):
    id: str
    type: str
    title: str
    status: Literal["pending", "generating", "completed", "failed", "skipped"] = "completed"
    source_unit_id: str | None = None
    source_outline_unit_id: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=dict)
    generation_info: Metadata = Field(default_factory=dict)
