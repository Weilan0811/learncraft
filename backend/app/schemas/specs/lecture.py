from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, SchemaModel
from app.schemas.specs.common import ElementReferenceBlock, RequiredElementSpec, TextBlock


LectureBlock = TextBlock | ElementReferenceBlock


class LectureSection(SchemaModel):
    id: str
    title: str
    summary: str
    outline_unit_id: str | None = None
    order: int | None = None
    learning_goal: str | None = None
    blocks: list[LectureBlock] = Field(default_factory=list)
    required_elements: list[RequiredElementSpec] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)


class LectureSpec(SchemaModel):
    id: str
    type: Literal["lecture"] = "lecture"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    objectives: list[str] = Field(default_factory=list)
    sections: list[LectureSection] = Field(default_factory=list)
    # TODO(MVP-lecture): Add summary, references, editable revision metadata,
    # and explicit required element declarations per section.
