"""
InteractiveHtmlRenderModel: frontend render contract for online interactive HTML.
"""

from typing import Literal

from pydantic import Field
from app.schemas.base import SchemaModel


class InteractiveHtmlRenderBlockRef(SchemaModel):
    block_id: str
    type: str
    title: str
    teaching_role: str
    interaction_ids: list[str] = Field(default_factory=list)


class InteractionRenderRef(SchemaModel):
    interaction_id: str
    section_id: str
    type: str
    target_concepts: list[str] = Field(default_factory=list)
    event_type: str


class InteractiveHtmlRenderedUnit(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    style_scope_id: str
    html_fragment: str
    css_fragment: str
    block_manifest: list[InteractiveHtmlRenderBlockRef] = Field(default_factory=list)
    interaction_manifest: list[InteractionRenderRef] = Field(default_factory=list)
    render_notes: dict = Field(default_factory=dict)


class InteractiveHtmlRenderSection(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    html_fragment: str
    block_refs: list[InteractiveHtmlRenderBlockRef] = Field(default_factory=list)


class NavigationItem(SchemaModel):
    section_id: str
    title: str
    anchor: str


class InteractiveRuntimeConfig(SchemaModel):
    progress_tracking: bool = True
    scoring_enabled: bool = True
    session_required: bool = True
    event_endpoint_template: str | None = "/api/interactive-lessons/{lesson_id}/sessions/{session_id}/events"


class InteractiveHtmlRenderModel(SchemaModel):
    render_type: str = "interactive_html_page"
    lesson_id: str
    title: str
    subtitle: str | None = None
    layout: Literal["vertical_lesson_with_tutor"] = "vertical_lesson_with_tutor"
    theme: dict = Field(default_factory=dict)
    navigation: list[NavigationItem] = Field(default_factory=list)
    interactions: list[InteractionRenderRef] = Field(default_factory=list)
    runtime: InteractiveRuntimeConfig = Field(default_factory=InteractiveRuntimeConfig)
    meta: dict = Field(default_factory=dict)
    pedagogy: dict = Field(default_factory=dict)
    sections: list[InteractiveHtmlRenderedUnit] = Field(default_factory=list)
    style_guide: dict = Field(default_factory=dict)
    citations: list[dict] = Field(default_factory=list)
