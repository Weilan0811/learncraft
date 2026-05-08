from typing import Literal

from pydantic import Field

from app.schemas.base import Metadata, MvpContentType, SchemaModel


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
    source_content_type: MvpContentType
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


LectureBlock = TextBlock | ElementReferenceBlock

SlideLayout = Literal[
    "cover",
    "section-divider",
    "title-content",
    "title-content-visual",
    "visual-left-content-right",
    "summary-cards",
]


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


class SlideSpecElement(SchemaModel):
    id: str
    type: str
    content: str | None = None
    element_id: str | None = None
    metadata: Metadata = Field(default_factory=dict)


class SlideSpecPage(SchemaModel):
    id: str
    outline_unit_id: str | None = None
    order: int | None = None
    title: str
    core_message: str
    layout: SlideLayout = "title-content"
    design_intent: str | None = None
    theme_variant: str | None = None
    layout_hints: Metadata = Field(default_factory=dict)
    elements: list[SlideSpecElement] = Field(default_factory=list)
    required_elements: list[RequiredElementSpec] = Field(default_factory=list)
    speaker_notes: str | None = None
    source_chunk_ids: list[str] = Field(default_factory=list)


class SlideDeckSpec(SchemaModel):
    id: str
    type: Literal["slide_deck"] = "slide_deck"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    slides: list[SlideSpecPage] = Field(default_factory=list)
    # TODO(MVP-slide): Add deck-level theme, slide count, speaker notes, and
    # asset dependency declarations for scene-content-kit/PPTX export.


ContentSpec = LectureSpec | SlideDeckSpec
# TODO(content-types): Extend this union when enabling social_post,
# podcast_script, video_script, project_task, quiz_pack, or learning_path.
