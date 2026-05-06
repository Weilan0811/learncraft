from pydantic import Field

from app.schemas.base import ElementType, MvpContentType, SchemaModel


class OutlineSection(SchemaModel):
    id: str
    title: str
    goal: str
    key_points: list[str] = Field(default_factory=list)
    recommended_elements: list[ElementType] = Field(default_factory=list)
    estimated_minutes: int | None = None
    assessment_points: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class Outline(SchemaModel):
    id: str
    content_type: MvpContentType
    title: str
    audience: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    sections: list[OutlineSection] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
