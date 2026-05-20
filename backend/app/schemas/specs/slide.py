import re
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import Metadata, SchemaModel
from app.schemas.specs.common import RequiredElementSpec


SlideLayout = Literal["image_text", "visual_summary"]

SlideElementRole = Literal[
    "title",
    "lead_card",
    "support_card",
    "summary_text",
    "visual",
]

IMAGE_TEXT_REQUIRED_ROLES: set[str] = {"title", "lead_card", "support_card", "summary_text", "visual"}
VISUAL_SUMMARY_REQUIRED_ROLES: set[str] = {"title", "summary_text", "visual"}
VISUAL_SUMMARY_OPTIONAL_ROLES: set[str] = set()

TITLE_MAX_CN = 20
EXPLANATION_MAX_SENTENCES = 2
BULLET_LIST_MIN = 2
BULLET_LIST_MAX = 4
BULLET_MAX_CN = 28
SUMMARY_TEXT_MAX_SENTENCES = 3
TAKEAWAY_MAX_CN = 32
CARD_LABEL_MAX_CN = 6
IMAGE_TEXT_SUMMARY_MAX_CN = 32
VISUAL_SUMMARY_SUMMARY_MAX_CN = 36


def _count_chinese_chars(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def _count_sentences(text: str) -> int:
    parts = re.split(r"[。！？；.!?;]", text)
    return sum(1 for p in parts if p.strip())


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
    layout: SlideLayout = "image_text"
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

        roles = [str(element.metadata.get("role") or "") for element in self.elements]

        if self.layout == "image_text":
            missing = IMAGE_TEXT_REQUIRED_ROLES - set(roles)
            if missing:
                raise ValueError(f"image_text layout requires roles: {missing}")
            extra = set(roles) - IMAGE_TEXT_REQUIRED_ROLES
            if extra:
                raise ValueError(f"image_text layout has unsupported roles: {extra}")
            card_roles = [role for role in roles if role in {"lead_card", "support_card"}]
            if card_roles.count("lead_card") != 1 or card_roles.count("support_card") != 1:
                raise ValueError("image_text layout requires exactly one lead_card and one support_card")
        elif self.layout == "visual_summary":
            missing = VISUAL_SUMMARY_REQUIRED_ROLES - set(roles)
            if missing:
                raise ValueError(f"visual_summary layout requires roles: {missing}")
            extra = set(roles) - VISUAL_SUMMARY_REQUIRED_ROLES
            if extra:
                raise ValueError(f"visual_summary layout has extra text card roles: {extra}")

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

        for element in self.elements:
            if element.type != "text" or not element.content:
                continue
            role = str(element.metadata.get("role") or "")
            if role == "title":
                if _count_chinese_chars(element.content) > TITLE_MAX_CN:
                    raise ValueError(f"title exceeds {TITLE_MAX_CN} chinese characters")
            elif role in {"lead_card", "support_card"}:
                display_label = str(element.metadata.get("display_label") or "")
                if not display_label:
                    raise ValueError(f"{role} requires display_label")
                if _count_chinese_chars(display_label) > CARD_LABEL_MAX_CN:
                    raise ValueError(f"{role} display_label exceeds {CARD_LABEL_MAX_CN} chinese characters")
                content_format = str(element.metadata.get("content_format") or "paragraph")
                if content_format not in {"paragraph", "bullets"}:
                    raise ValueError(f"{role} content_format must be paragraph or bullets")
                if content_format == "paragraph":
                    if _count_sentences(element.content) > EXPLANATION_MAX_SENTENCES:
                        raise ValueError(f"{role} paragraph exceeds {EXPLANATION_MAX_SENTENCES} sentences")
                else:
                    lines = [line.strip() for line in element.content.splitlines() if line.strip()]
                    max_items = BULLET_LIST_MAX if role == "support_card" else 3
                    if len(lines) < 1 or len(lines) > max_items:
                        raise ValueError(f"{role} bullets must have 1-{max_items} items")
                    for line in lines:
                        if _count_chinese_chars(line) > BULLET_MAX_CN:
                            raise ValueError(f"{role} bullet item exceeds {BULLET_MAX_CN} chinese characters: {line[:20]}")
            elif role == "explanation":
                if _count_sentences(element.content) > EXPLANATION_MAX_SENTENCES:
                    raise ValueError(f"explanation exceeds {EXPLANATION_MAX_SENTENCES} sentences")
            elif role == "bullet_list":
                lines = [line.strip() for line in element.content.splitlines() if line.strip()]
                if len(lines) < BULLET_LIST_MIN or len(lines) > BULLET_LIST_MAX:
                    raise ValueError(f"bullet_list must have {BULLET_LIST_MIN}-{BULLET_LIST_MAX} items")
                for line in lines:
                    if _count_chinese_chars(line) > BULLET_MAX_CN:
                        raise ValueError(f"bullet item exceeds {BULLET_MAX_CN} chinese characters: {line[:20]}")
            elif role == "summary_text":
                max_cn = IMAGE_TEXT_SUMMARY_MAX_CN if self.layout == "image_text" else VISUAL_SUMMARY_SUMMARY_MAX_CN
                if _count_chinese_chars(_strip_summary_prefix(element.content)) > max_cn:
                    raise ValueError(f"summary_text exceeds {max_cn} chinese characters")
                if _has_summary_prefix(element.content):
                    raise ValueError("summary_text must not include fixed summary prefix")
            elif role == "takeaway":
                if _count_chinese_chars(element.content) > TAKEAWAY_MAX_CN:
                    raise ValueError(f"takeaway exceeds {TAKEAWAY_MAX_CN} chinese characters")

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


def _has_summary_prefix(text: str) -> bool:
    return bool(re.match(r"^\s*(核心点|总结|结论)\s*[:：]", text))


def _strip_summary_prefix(text: str) -> str:
    return re.sub(r"^\s*(核心点|总结|结论)\s*[:：]\s*", "", text).strip()


class SlideDeckSpec(SchemaModel):
    id: str
    type: Literal["slide_deck"] = "slide_deck"
    version: str = "content.spec/v1"
    title: str
    metadata: Metadata = Field(default_factory=dict)
    slides: list[SlideSpecPage] = Field(default_factory=list)
