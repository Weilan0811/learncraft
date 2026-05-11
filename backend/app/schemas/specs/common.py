from typing import Literal

from pydantic import Field

from app.schemas.base import ContentType, Metadata, SchemaModel


class RetryPolicy(SchemaModel):
    max_retries: int = 2
    fallback_strategy: str = "placeholder_asset"


class RequiredElementSpec(SchemaModel):
    element_id: str
    type: Literal["image", "mindmap"]
    title: str
    purpose: str
    instruction: str
    style: str | None = None
    aspect_ratio: str | None = None
    source_unit_id: str
    source_outline_unit_id: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    priority: Literal["low", "medium", "high"] = "medium"


class ElementRequest(SchemaModel):
    element_id: str
    type: Literal["image", "mindmap"]
    title: str
    purpose: str
    instruction: str
    source_content_type: ContentType
    source_unit_id: str
    source_outline_unit_id: str
    source_chunk_ids: list[str] = Field(default_factory=list)
    context: Metadata = Field(default_factory=dict)
    constraints: Metadata = Field(default_factory=dict)
    render_hints: Metadata = Field(default_factory=dict)
    priority: Literal["low", "medium", "high"] = "medium"
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class BaseBlock(SchemaModel):
    id: str
    type: str
    title: str
    citations: list[str] = Field(default_factory=list)


class TextBlock(BaseBlock):
    type: Literal["text"] = "text"
    content: str


class ElementReferenceBlock(BaseBlock):
    type: Literal["element_ref"] = "element_ref"
    element_id: str
