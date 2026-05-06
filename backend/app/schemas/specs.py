from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel


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


LectureBlock = TextBlock | ElementReferenceBlock


class LectureSection(SchemaModel):
    id: str
    title: str
    summary: str
    blocks: list[LectureBlock] = Field(default_factory=list)


class LectureSpec(SchemaModel):
    id: str
    type: Literal["lecture"] = "lecture"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    objectives: list[str] = Field(default_factory=list)
    sections: list[LectureSection] = Field(default_factory=list)


class SlideSpecElement(SchemaModel):
    id: str
    type: str
    content: str | None = None
    element_id: str | None = None
    metadata: Metadata = Field(default_factory=dict)


class SlideSpecPage(SchemaModel):
    id: str
    title: str
    core_message: str
    layout: str = "title-content"
    elements: list[SlideSpecElement] = Field(default_factory=list)


class SlideDeckSpec(SchemaModel):
    id: str
    type: Literal["slide_deck"] = "slide_deck"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    slides: list[SlideSpecPage] = Field(default_factory=list)


ContentSpec = LectureSpec | SlideDeckSpec
