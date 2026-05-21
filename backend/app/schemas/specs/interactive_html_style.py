from typing import Literal

from pydantic import Field

from app.schemas.base import SchemaModel


class InteractiveHtmlCourseStyleGuide(SchemaModel):
    style_id: str
    layout_mode: Literal["vertical_lesson_with_tutor"] = "vertical_lesson_with_tutor"
    visual_keywords: list[str] = Field(default_factory=list)
    color_tokens: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    component_motifs: list[str] = Field(default_factory=list)
    interaction_style: dict[str, str] = Field(default_factory=dict)
    animation_style: dict[str, str] = Field(default_factory=dict)
    spacing_density: Literal["compact", "medium", "relaxed"] = "medium"
    avoid: list[str] = Field(default_factory=list)


DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE = InteractiveHtmlCourseStyleGuide(
    style_id="warm_tutor_card_v1",
    layout_mode="vertical_lesson_with_tutor",
    visual_keywords=["温和", "卡片式", "流程清晰", "轻量动画"],
    color_tokens={
        "background": "#f7f4ef",
        "surface": "#ffffff",
        "primary": "#5b6cff",
        "accent": "#ffb86b",
        "text": "#1f2937",
    },
    component_motifs=[
        "rounded cards",
        "soft shadow",
        "dotted connector",
        "teacher speech bubble",
        "step badges",
    ],
    avoid=[
        "dense tables",
        "tiny text",
        "large empty space",
        "unbalanced two-column layout",
        "unscoped css",
    ],
)
