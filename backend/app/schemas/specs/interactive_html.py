"""
Interactive HTML schemas.

The online lesson contract uses constrained, sanitized HTML fragments per
section. The frontend owns the shell, CSS, navigation, and interaction runtime.

P0 refactor: Unit Spec focuses on teaching design (no HTML).
Render stage produces HTML + CSS via LLM Composer.
"""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import SchemaModel


class CitationRef(SchemaModel):
    source_id: str
    chunk_id: str | None = None
    excerpt: str | None = None


class AssetRef(SchemaModel):
    asset_id: str
    asset_type: Literal["image", "css", "js"] = "image"
    url: str | None = None


class ConceptRef(SchemaModel):
    concept_id: str
    name: str
    description: str | None = None


class InteractiveHtmlTeachingBlock(SchemaModel):
    block_id: str
    block_type: Literal[
        "intro",
        "concept_explanation",
        "case_compare",
        "animated_flow",
        "context_inspector",
        "stepper",
        "socratic_chat",
        "scenario",
        "scenario_discussion",
        "single_choice",
        "multiple_choice",
        "short_answer",
        "drag_match",
        "sequence",
        "reflection",
        "summary",
    ]
    title: str
    teaching_role: str
    content_goal: str
    must_cover: list[str] = Field(default_factory=list)
    suggested_expression: str | None = None
    interaction_id: str | None = None
    source_refs: list[str] = Field(default_factory=list)


class InteractiveHtmlInteractionOption(SchemaModel):
    id: str
    text: str
    is_correct: bool | None = None
    feedback: str | None = None


class InteractiveHtmlInteractionSpec(SchemaModel):
    interaction_id: str
    block_id: str
    type: Literal[
        "single_choice",
        "multiple_choice",
        "short_answer",
        "scenario_discussion",
    ]
    event_type: Literal[
        "single_choice_answered",
        "multiple_choice_answered",
        "short_answer_submitted",
        "scenario_discussion_submitted",
    ]
    target_concepts: list[str] = Field(default_factory=list)
    prompt: str | None = None
    options: list[InteractiveHtmlInteractionOption] = Field(default_factory=list)
    feedback_policy: Literal["local", "submit_to_backend", "local_and_submit"] = "local_and_submit"
    placeholder: str | None = None
    reference_points: list[str] = Field(default_factory=list)
    min_length: int | None = None
    scenario: dict[str, Any] = Field(default_factory=dict)
    visual_variant: Literal[
        "diagnostic_card",
        "checkpoint",
        "tutor_question",
        "challenge_box",
        "scenario_decision",
    ] | None = None
    allow_adaptive_followup: bool = True

    @field_validator("scenario", mode="before")
    @classmethod
    def normalize_null_scenario(cls, value: object) -> object:
        return {} if value is None else value


class InteractiveHtmlInteractionRef(SchemaModel):
    interaction_id: str
    type: Literal[
        "single_choice",
        "multiple_choice",
        "short_answer",
        "drag_match",
        "sequence",
        "socratic_chat",
        "scenario",
        "complete_section",
        "tab_select",
        "flow_control",
    ]
    event_type: str
    target_concepts: list[str] = Field(default_factory=list)


class InteractiveHtmlBlockRef(SchemaModel):
    block_id: str
    type: Literal[
        "intro",
        "concept",
        "explain",
        "visual",
        "case_compare",
        "flow",
        "tabs",
        "scenario",
        "dialogue",
        "quiz",
        "practice",
        "reflection",
        "summary",
    ]
    title: str
    teaching_role: str
    interaction_ids: list[str] = Field(default_factory=list)


class InteractiveHtmlSectionReference(SchemaModel):
    """Used inside outline: defines section skeleton, no rendering body."""

    section_id: str
    title: str
    learning_goal: str
    target_concepts: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class InteractiveHtmlOutline(SchemaModel):
    content_type: Literal["interactive_html"] = "interactive_html"
    title: str
    lesson_goal: str
    audience: str
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    estimated_minutes: int | None = None
    sections: list[InteractiveHtmlSectionReference] = Field(default_factory=list)


class InteractiveHtmlSectionSpec(SchemaModel):
    section_id: str
    title: str
    learning_goal: str
    narrative_goal: str = ""
    teaching_flow: list[InteractiveHtmlTeachingBlock] = Field(default_factory=list)
    interaction_specs: list[InteractiveHtmlInteractionSpec] = Field(default_factory=list)
    concepts: list[ConceptRef] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)


class InteractiveHtmlPedagogy(SchemaModel):
    tutor_tone: Literal["guided", "encouraging", "socratic"] = "guided"
    interaction_density: Literal["low", "medium", "high"] = "medium"
    terminology_level: Literal["low", "medium", "high"] = "medium"


class InteractiveHtmlExportOptions(SchemaModel):
    interactive_html: bool = True
    zip: bool = False


class InteractiveHtmlMeta(SchemaModel):
    language: str = "zh-CN"
    audience: str
    difficulty: Literal["introductory", "intermediate", "advanced"] = "introductory"
    estimated_minutes: int | None = None


class InteractiveHtmlSpec(SchemaModel):
    content_type: Literal["interactive_html"] = "interactive_html"
    lesson_id: str
    title: str
    subtitle: str | None = None
    meta: InteractiveHtmlMeta
    pedagogy: InteractiveHtmlPedagogy = Field(default_factory=InteractiveHtmlPedagogy)
    sections: list[InteractiveHtmlSectionSpec] = Field(default_factory=list)
    citations: list[CitationRef] = Field(default_factory=list)
    assets: list[AssetRef] = Field(default_factory=list)
    export_options: InteractiveHtmlExportOptions = Field(default_factory=InteractiveHtmlExportOptions)


class InteractiveHtmlElementPolicy(SchemaModel):
    generate_process_images: bool = False
    generate_mindmaps: bool = False
    generated_assets: list[str] = Field(default_factory=list)
