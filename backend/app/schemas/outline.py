from typing import Literal

from pydantic import Field

from app.schemas.base import ContentType, SchemaModel


class OutlineUnit(SchemaModel):
    id: str
    order: int
    unit_type: Literal["section", "slide"]
    title: str
    goal: str
    core_message: str
    key_points: list[str] = Field(default_factory=list)
    visual_strategy: str | None = None
    retrieval_queries: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)


class OutlineSection(SchemaModel):
    id: str
    title: str
    goal: str
    key_points: list[str] = Field(default_factory=list)
    estimated_minutes: int | None = None
    assessment_points: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class Outline(SchemaModel):
    id: str
    content_type: ContentType
    title: str
    audience: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    units: list[OutlineUnit] = Field(default_factory=list)
    sections: list[OutlineSection] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
