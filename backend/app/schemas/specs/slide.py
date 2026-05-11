from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import Metadata, SchemaModel
from app.schemas.specs.common import RequiredElementSpec


SlideLayout = Literal[
    "cover",
    "section-divider",
    "title-content",
    "title-content-visual",
    "visual-left-content-right",
    "summary-cards",
]


class SlideSpecElement(SchemaModel):
    id: str
    type: Literal["text", "element_ref"]
    content: str | None = None
    element_id: str | None = None
    metadata: Metadata = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload_for_type(self) -> "SlideSpecElement":
        if self.type == "text" and not self.content:
            raise ValueError("text slide elements require content")
        if self.type == "element_ref" and not self.element_id:
            raise ValueError("element_ref slide elements require element_id")
        return self


class SlideSpecPage(SchemaModel):
    id: str
    outline_unit_id: str
    order: int
    title: str
    core_message: str
    layout: SlideLayout = "title-content"
    design_intent: str
    theme_variant: str | None = None
    layout_hints: Metadata = Field(default_factory=dict)
    elements: list[SlideSpecElement] = Field(default_factory=list)
    required_elements: list[RequiredElementSpec] = Field(default_factory=list)
    speaker_notes: str
    source_chunk_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_workflow_contract(self) -> "SlideSpecPage":
        expected_id = f"slide_{self.outline_unit_id}"
        if self.id != expected_id:
            raise ValueError(f"slide id must be {expected_id}")
        outline_order = _trailing_order(self.outline_unit_id)
        if outline_order is not None and self.order != outline_order:
            raise ValueError("slide order must match outline_unit_id numeric suffix")
        if self.layout_hints.get("supported_renderer") != "scenekit.slide/v1":
            raise ValueError("layout_hints.supported_renderer must be scenekit.slide/v1")

        roles = [element.metadata.get("role") for element in self.elements]
        if "title" not in roles:
            raise ValueError("slide elements must include a title role")
        if "body" not in roles:
            raise ValueError("slide elements must include a body role")

        required_ids = {item.element_id for item in self.required_elements}
        if len(required_ids) != len(self.required_elements):
            raise ValueError("required element ids must be unique")
        for element in self.elements:
            if element.type == "element_ref" and element.element_id not in required_ids:
                raise ValueError(f"element_ref {element.element_id} is missing from required_elements")
        for item in self.required_elements:
            if item.source_unit_id != self.id:
                raise ValueError(f"required element {item.element_id} source_unit_id must match slide id")
            if item.source_outline_unit_id != self.outline_unit_id:
                raise ValueError(f"required element {item.element_id} source_outline_unit_id must match slide outline_unit_id")

        return self


def _trailing_order(value: str) -> int | None:
    digits = []
    for character in reversed(value):
        if not character.isdigit():
            break
        digits.append(character)
    if not digits:
        return None
    return int("".join(reversed(digits)))


class SlideDeckSpec(SchemaModel):
    id: str
    type: Literal["slide_deck"] = "slide_deck"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    slides: list[SlideSpecPage] = Field(default_factory=list)
    # TODO(MVP-slide): Add deck-level theme, slide count, speaker notes, and
    # asset dependency declarations for scene-content-kit/PPTX export.
