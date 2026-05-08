import json
import os
from typing import cast

from app.core.config import get_settings
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
from app.services.llm_service import get_llm_service


def build_lecture_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> LectureSection:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return build_lecture_unit_spec_fallback(state, unit, chunk_ids)

    try:
        return generate_lecture_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        return build_lecture_unit_spec_fallback(state, unit, chunk_ids)


def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage:
    settings = get_settings()

    if settings.provider_mode == "stub":
        return build_slide_unit_spec_fallback(state, unit, chunk_ids)

    try:
        return generate_slide_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        return build_slide_unit_spec_fallback(state, unit, chunk_ids)


def generate_lecture_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> LectureSection:
    unit_spec_id = f"lecture_{unit.id}"
    prompt = _build_unit_spec_prompt("lecture", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(LectureSection, llm_service.generate_structured(prompt=prompt, schema=LectureSection))


def generate_slide_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    unit_spec_id = f"slide_{unit.id}"
    prompt = _build_unit_spec_prompt("slide_deck", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(SlideSpecPage, llm_service.generate_structured(prompt=prompt, schema=SlideSpecPage))


def _build_unit_spec_prompt(
    content_type: str,
    state: ContentGenerationState,
    unit: OutlineUnit,
    unit_spec_id: str,
    chunk_ids: list[str],
) -> str:
    template_path = _get_unit_spec_template_path(content_type)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    retrieval_results = _format_retrieval_results(state.current_unit_context or [])
    generation_options = json.dumps(state.normalized_request, ensure_ascii=False, indent=2)
    outline_unit_json = json.dumps(unit.model_dump(), ensure_ascii=False, indent=2)

    return template.format(
        unit_spec_id=unit_spec_id,
        outline_unit=outline_unit_json,
        retrieval_results=retrieval_results,
        generation_options=generation_options,
    )


def _get_unit_spec_template_path(content_type: str) -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts", "generator")
    if content_type == "slide_deck":
        return os.path.join(prompts_dir, "slide_deck_spec.md")
    return os.path.join(prompts_dir, "lecture_spec.md")


def _format_retrieval_results(chunks: list) -> str:
    if not chunks:
        return "No retrieval results."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_id = getattr(chunk, "id", f"chunk_{i}")
        source_title = getattr(chunk, "source_title", "")
        score = getattr(chunk, "score", 0.0)
        content = getattr(chunk, "content", "")[:500]
        formatted.append(f"[chunk_id={chunk_id}]")
        if source_title:
            formatted.append(f"source_title: {source_title}")
        formatted.append(f"score: {score}")
        formatted.append(f"content: {content}")
        formatted.append("")

    return "\n".join(formatted)


def build_lecture_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> LectureSection:
    section_id = f"lecture_{unit.id}"
    options = state.normalized_request or {}
    include_images = bool(options.get("include_images", True))
    include_mindmap = bool(options.get("include_mindmap", False))

    required_elements: list[RequiredElementSpec] = []
    blocks = [
        TextBlock(
            id=f"{section_id}_intro",
            title=f"{unit.title}: core idea",
            content=(
                f"{unit.core_message}\n\n"
                f"This section helps learners reach the goal: {unit.goal}. Start from the core idea, then connect each "
                "detail back to the larger learning path."
            ),
            citations=chunk_ids,
        )
    ]

    if include_images:
        image_spec = _image_spec_for_unit(
            unit=unit,
            unit_spec_id=section_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            aspect_ratio="4:3",
            style=str(options.get("image_style") or "clean educational illustration"),
            purpose="Use a visual only where it makes the concept easier to understand than text alone.",
            instruction=(
                f"Create a local illustration asset for '{unit.title}', meant to be embedded inside a lecture section. "
                f"Show the core message: {unit.core_message}. Use a focused diagram, timeline, process graphic, or "
                "concept illustration with a clear hierarchy and concise labels. Do not create a full presentation slide, "
                "slide title, banner, footer, agenda, summary panel, or page-like teaching layout. Avoid decorative "
                "backgrounds, tiny text, unrelated people, and vague stock imagery."
            ),
        )
        required_elements.append(image_spec)
        blocks.append(
            ElementReferenceBlock(
                id=f"{section_id}_image_ref",
                title=image_spec.title,
                element_id=image_spec.element_id,
            )
        )

    points = unit.key_points or ["core concept", "key relationship", "application scenario"]
    blocks.append(
        TextBlock(
            id=f"{section_id}_details",
            title=f"{unit.title}: detailed explanation",
            content="\n\n".join(
                f"{index}. {point}: explain what this means, why it matters, and how it connects to '{unit.title}'."
                for index, point in enumerate(points, 1)
            ),
            citations=chunk_ids,
        )
    )

    if include_mindmap:
        mindmap_spec = _mindmap_spec_for_unit(
            unit=unit,
            unit_spec_id=section_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            purpose="Summarize the structure only when the section has several related concepts.",
            instruction=(
                f"Create Markmap-compatible Markdown with root '{unit.title}'. Use at most 3 levels and 3-5 first-level "
                "branches covering definitions, key points, relationships, and applications. Keep node labels short."
            ),
        )
        required_elements.append(mindmap_spec)
        blocks.append(
            ElementReferenceBlock(
                id=f"{section_id}_mindmap_ref",
                title=mindmap_spec.title,
                element_id=mindmap_spec.element_id,
            )
        )

    blocks.append(
        TextBlock(
            id=f"{section_id}_summary",
            title=f"{unit.title}: wrap-up",
            content=(
                f"After this section, learners should be able to restate '{unit.core_message}' in their own words and "
                "use the listed points as a compact review framework."
            ),
            citations=chunk_ids,
        )
    )

    return LectureSection(
        id=section_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        summary=unit.core_message,
        learning_goal=unit.goal,
        source_chunk_ids=chunk_ids,
        required_elements=required_elements,
        blocks=blocks,
    )


def build_slide_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    slide_id = f"slide_{unit.id}"
    options = state.normalized_request or {}
    include_images = bool(options.get("include_images", True))
    include_mindmap = bool(options.get("include_mindmap", False))
    layout = _choose_slide_layout(unit)

    required_elements: list[RequiredElementSpec] = []
    elements = [
        SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title, metadata={"role": "title"}),
        SlideSpecElement(
            id=f"{slide_id}_body",
            type="text",
            content=unit.core_message,
            metadata={"role": "body", "emphasis": "primary"},
        ),
    ]
    layout_hints: dict[str, object] = {
        "density": "balanced",
        "supported_renderer": "scenekit.slide/v1",
    }

    if include_images:
        image_spec = _image_spec_for_unit(
            unit=unit,
            unit_spec_id=slide_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            aspect_ratio="16:9",
            style=str(options.get("image_style") or "clean educational illustration"),
            purpose="Support the slide's single core message with a simple teaching visual.",
            instruction=(
                f"Create a local illustration asset for '{unit.title}', meant to be placed inside a slide rather than "
                f"serve as the slide itself. Focus on: {unit.core_message}. Use one clear diagram, timeline, process "
                "graphic, or concept illustration with concise labels. Do not create a full presentation slide, title "
                "bar, footer, agenda, bullet list panel, or summary strip."
            ),
        )
        required_elements.append(image_spec)
        layout_hints["primary_visual"] = image_spec.element_id
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_image_ref",
                type="element_ref",
                element_id=image_spec.element_id,
                metadata={"role": "visual", "placement": "primary"},
            )
        )

    if include_mindmap:
        mindmap_spec = _mindmap_spec_for_unit(
            unit=unit,
            unit_spec_id=slide_id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            purpose="Show relationships among slide concepts only when helpful.",
            instruction=(
                f"Create Markmap-compatible Markdown with root '{unit.title}', at most 3 levels, and 3-5 branches. "
                "Use short labels suitable for a slide."
            ),
        )
        required_elements.append(mindmap_spec)
        layout_hints["secondary_visual"] = mindmap_spec.element_id
        elements.append(
            SlideSpecElement(
                id=f"{slide_id}_mindmap_ref",
                type="element_ref",
                element_id=mindmap_spec.element_id,
                metadata={"role": "mindmap", "placement": "supporting", "downgrade": "text"},
            )
        )

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout=layout,
        design_intent=_design_intent_for_layout(layout),
        theme_variant="teaching-clean",
        layout_hints=layout_hints,
        required_elements=required_elements,
        speaker_notes=f"Explain this slide around the goal: {unit.goal}.",
        source_chunk_ids=chunk_ids,
        elements=elements,
    )


def _image_spec_for_unit(
    unit: OutlineUnit,
    unit_spec_id: str,
    request_id: str,
    chunk_ids: list[str],
    aspect_ratio: str,
    style: str,
    purpose: str,
    instruction: str,
) -> RequiredElementSpec:
    return RequiredElementSpec(
        element_id=f"image_{request_id}_{unit.id}",
        type="image",
        title=f"{unit.title} visual explanation",
        purpose=purpose,
        instruction=instruction,
        style=style,
        aspect_ratio=aspect_ratio,
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="high",
    )


def _mindmap_spec_for_unit(
    unit: OutlineUnit,
    unit_spec_id: str,
    request_id: str,
    chunk_ids: list[str],
    purpose: str,
    instruction: str,
) -> RequiredElementSpec:
    return RequiredElementSpec(
        element_id=f"mindmap_{request_id}_{unit.id}",
        type="mindmap",
        title=f"{unit.title} knowledge map",
        purpose=purpose,
        instruction=instruction,
        source_unit_id=unit_spec_id,
        source_outline_unit_id=unit.id,
        source_chunk_ids=chunk_ids,
        priority="medium",
    )


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
