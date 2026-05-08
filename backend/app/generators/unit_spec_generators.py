from app.schemas.outline import OutlineUnit
from app.schemas.specs import (
    ElementReferenceBlock,
    LectureSection,
    RequiredElementSpec,
    SlideSpecElement,
    SlideSpecPage,
    TextBlock,
)
from app.schemas.state import ContentGenerationState


def build_lecture_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> LectureSection:
    section_id = f"lecture_{unit.id}"
    image, mindmap = required_elements_for_unit(
        unit=unit,
        unit_spec_id=section_id,
        content_type=state.content_type,
        chunk_ids=chunk_ids,
        request_id=state.request_id,
    )
    return LectureSection(
        id=section_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        summary=unit.core_message,
        learning_goal=unit.goal,
        source_chunk_ids=chunk_ids,
        required_elements=[image, mindmap],
        blocks=[
            TextBlock(
                id=f"{section_id}_text",
                title=unit.title,
                content=f"{unit.core_message}\n\n" + "\n".join(f"- {point}" for point in unit.key_points),
                citations=chunk_ids,
            ),
            ElementReferenceBlock(id=f"{section_id}_image_ref", title=image.title, element_id=image.element_id),
            ElementReferenceBlock(id=f"{section_id}_mindmap_ref", title=mindmap.title, element_id=mindmap.element_id),
        ],
    )


def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage:
    slide_id = f"slide_{unit.id}"
    image, mindmap = required_elements_for_unit(
        unit=unit,
        unit_spec_id=slide_id,
        content_type=state.content_type,
        chunk_ids=chunk_ids,
        request_id=state.request_id,
    )
    layout = _choose_slide_layout(unit)
    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout=layout,
        design_intent=_design_intent_for_layout(layout),
        theme_variant="teaching-clean",
        layout_hints={
            "density": "balanced",
            "primary_visual": image.element_id,
            "secondary_visual": mindmap.element_id,
            "supported_renderer": "scenekit.slide/v1",
        },
        required_elements=[image, mindmap],
        speaker_notes=f"围绕 {unit.goal} 展开讲解。",
        source_chunk_ids=chunk_ids,
        elements=[
            SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title, metadata={"role": "title"}),
            SlideSpecElement(
                id=f"{slide_id}_body",
                type="text",
                content=unit.core_message,
                metadata={"role": "body", "emphasis": "primary"},
            ),
            SlideSpecElement(
                id=f"{slide_id}_image_ref",
                type="element_ref",
                element_id=image.element_id,
                metadata={"role": "visual", "placement": "primary"},
            ),
            SlideSpecElement(
                id=f"{slide_id}_mindmap_ref",
                type="element_ref",
                element_id=mindmap.element_id,
                metadata={"role": "mindmap", "placement": "supporting", "downgrade": "text"},
            ),
        ],
    )


def required_elements_for_unit(
    unit: OutlineUnit,
    unit_spec_id: str,
    content_type: str,
    chunk_ids: list[str],
    request_id: str = "stub",
) -> tuple[RequiredElementSpec, RequiredElementSpec]:
    image = RequiredElementSpec(
        element_id=f"image_{request_id}_{unit.id}",
        type="image",
        title=f"{unit.title} 示意图",
        purpose="作为内容主视觉",
        instruction=f"生成一张适合教学预览的简洁示意图，主题为：{unit.core_message}",
        style="clean educational illustration",
        aspect_ratio="16:9" if content_type == "slide_deck" else "4:3",
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="high",
    )
    mindmap = RequiredElementSpec(
        element_id=f"mindmap_{request_id}_{unit.id}",
        type="mindmap",
        title=f"{unit.title} 知识结构",
        purpose="梳理本单元知识结构",
        instruction="根据本单元内容生成三层以内的 Markdown 思维导图。",
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="medium",
    )
    return image, mindmap


def _choose_slide_layout(unit: OutlineUnit) -> str:
    supported = {
        "cover",
        "section-divider",
        "title-content",
        "title-content-visual",
        "visual-left-content-right",
        "summary-cards",
    }
    if unit.visual_strategy in supported:
        return unit.visual_strategy
    if unit.order == 1:
        return "cover"
    if len(unit.key_points) >= 4:
        return "summary-cards"
    if unit.order % 2 == 0:
        return "visual-left-content-right"
    return "title-content-visual"


def _design_intent_for_layout(layout: str) -> str:
    intents = {
        "cover": "Open the deck with a clear topic signal and one concise message.",
        "section-divider": "Separate the deck into a new conceptual section.",
        "title-content": "Explain one idea with a strong title and readable message block.",
        "title-content-visual": "Pair the core explanation with a supporting teaching visual.",
        "visual-left-content-right": "Lead with a visual and explain it in a compact text panel.",
        "summary-cards": "Summarize several key points as scan-friendly visual cards.",
    }
    return intents.get(layout, intents["title-content-visual"])
