"""
InteractiveHtmlRenderModel: frontend render contract for online interactive HTML.
"""

from pydantic import Field
from app.schemas.base import Metadata, SchemaModel


class InteractiveHtmlRenderBlock(SchemaModel):
    """Generic render block carrying full block data for frontend rendering.

    The `block_data` dict preserves the complete LessonBlock fields so the
    frontend components can render each block type without backend coupling.
    """
    block_id: str
    type: str
    title: str | None = None
    block_data: dict = Field(default_factory=dict)
    metadata: Metadata = Field(default_factory=dict)


class InteractiveHtmlRenderSection(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    render_blocks: list[InteractiveHtmlRenderBlock] = Field(default_factory=list)


class InteractiveHtmlRenderModel(SchemaModel):
    render_type: str = "interactive_html_page"
    lesson_id: str
    title: str
    subtitle: str | None = None
    meta: dict = Field(default_factory=dict)
    pedagogy: dict = Field(default_factory=dict)
    sections: list[InteractiveHtmlRenderSection] = Field(default_factory=list)
    citations: list[dict] = Field(default_factory=list)
