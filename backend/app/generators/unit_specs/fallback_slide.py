from app.generators.unit_specs.slide_layout import choose_slide_layout, design_intent_for_layout
from app.schemas.outline import OutlineUnit
from app.schemas.specs import (
    BULLET_LIST_MAX,
    BULLET_LIST_MIN,
    BULLET_MAX_CN,
    IMAGE_TEXT_SUMMARY_MAX_CN,
    RequiredElementSpec,
    SlideSpecElement,
    SlideSpecPage,
    TITLE_MAX_CN,
)
from app.schemas.state import ContentGenerationState


def build_slide_unit_spec_fallback(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    slide_id = f"slide_{unit.id}"
    layout = choose_slide_layout(unit)
    options = state.normalized_request or {}

    if layout == "visual_summary":
        return _build_visual_summary_fallback(slide_id, unit, state, chunk_ids, options)

    return _build_image_text_fallback(slide_id, unit, state, chunk_ids, options)


def _build_image_text_fallback(
    slide_id: str,
    unit: OutlineUnit,
    state: ContentGenerationState,
    chunk_ids: list[str],
    options: dict[str, object],
) -> SlideSpecPage:
    image_id = f"image_{state.request_id}_{unit.id}"
    points = unit.key_points[:BULLET_LIST_MAX] if unit.key_points else ["核心概念", "关键关系"]
    bullet_content = "\n".join(f"• {p[:BULLET_MAX_CN]}" for p in points)
    if len(points) < BULLET_LIST_MIN:
        while len(points) < BULLET_LIST_MIN:
            bullet_content += "\n• …"
            points.append("…")

    elements = [
        SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"}),
        SlideSpecElement(
            id=f"{slide_id}_lead_card",
            type="text",
            content=unit.core_message,
            metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
        ),
        SlideSpecElement(
            id=f"{slide_id}_support_card",
            type="text",
            content=bullet_content,
            metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
        ),
        SlideSpecElement(id=f"{slide_id}_summary_text", type="text", content=unit.core_message[:IMAGE_TEXT_SUMMARY_MAX_CN], metadata={"role": "summary_text"}),
        SlideSpecElement(id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id, metadata={"role": "visual", "placement": "primary"}),
    ]

    required_elements = [
        RequiredElementSpec(
            element_id=image_id,
            type="image",
            title=f"{unit.title} illustration",
            purpose="Support the image_text slide with a low-density teaching visual.",
            instruction=(
                "Create a low-density teaching illustration asset for a slide, not a full slide. "
                "The image will appear in a medium-sized right-side panel. "
                "Show one clear scene, object, metaphor, or simple action. "
                "Use realistic illustration, hand-drawn sketch, or clean educational illustration style. "
                "No title bar, no header, no footer, no slide border, no lecture card layout. "
                "No infographic. No flowchart. No architecture diagram. No mind map. "
                "No dense arrows. No multiple panels. No small text. "
                "Use at most 1-3 short labels only if necessary. "
                "The image must remain readable in a compact slide image area. "
                f"Topic: {unit.title}. Core message: {unit.core_message}."
            ),
            style=str(options.get("image_style") or "clean educational illustration, realistic diagram"),
            aspect_ratio="4:3",
            source_unit_id=slide_id,
            source_outline_unit_id=unit.id,
            source_chunk_ids=chunk_ids,
            priority="high",
        ),
    ]

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout="image_text",
        design_intent=design_intent_for_layout("image_text"),
        theme_variant="teaching-clean",
        layout_hints={"density": "balanced", "supported_renderer": "scenekit.slide/v1", "primary_visual": image_id},
        required_elements=required_elements,
        speaker_notes=f"Explain this slide around the goal: {unit.goal}.",
        source_chunk_ids=chunk_ids,
        elements=elements,
    )


def _build_visual_summary_fallback(
    slide_id: str,
    unit: OutlineUnit,
    state: ContentGenerationState,
    chunk_ids: list[str],
    options: dict[str, object],
) -> SlideSpecPage:
    image_id = f"image_{state.request_id}_{unit.id}"

    elements = [
        SlideSpecElement(id=f"{slide_id}_title", type="text", content=unit.title[:TITLE_MAX_CN], metadata={"role": "title"}),
        SlideSpecElement(id=f"{slide_id}_summary_text", type="text", content=unit.core_message, metadata={"role": "summary_text"}),
        SlideSpecElement(id=f"{slide_id}_visual_ref", type="element_ref", element_id=image_id, metadata={"role": "visual", "placement": "primary"}),
    ]

    required_elements = [
        RequiredElementSpec(
            element_id=image_id,
            type="image",
            title=f"{unit.title} summary diagram",
            purpose="Support the visual_summary slide with a structured summary diagram.",
            instruction=(
                "Create a wide landscape summary diagram asset for the upper area of a teaching slide, not a full slide. "
                "Use a clear framework diagram, flowchart, process diagram, or structured summary diagram. "
                "The diagram should fit a wide horizontal canvas. "
                "Keep the main content inside a centered safe area with generous margins. "
                "Use 3-5 major nodes and at most 2 hierarchy levels. "
                "Use large readable labels with at most one short line per node. "
                "No outer title, no top banner, no footer, no bottom explanation bar, no slide border. "
                "Avoid numbered large cards, dense arrows, dense small text, poster layout, and full PowerPoint slide screenshot. "
                f"Topic: {unit.title}. Core message: {unit.core_message}."
            ),
            style=str(options.get("image_style") or "infographic, flowchart, framework diagram"),
            aspect_ratio="21:9",
            source_unit_id=slide_id,
            source_outline_unit_id=unit.id,
            source_chunk_ids=chunk_ids,
            priority="high",
        ),
    ]

    return SlideSpecPage(
        id=slide_id,
        outline_unit_id=unit.id,
        order=unit.order,
        title=unit.title,
        core_message=unit.core_message,
        layout="visual_summary",
        design_intent=design_intent_for_layout("visual_summary"),
        theme_variant="teaching-clean",
        layout_hints={"density": "rich", "supported_renderer": "scenekit.slide/v1", "primary_visual": image_id},
        required_elements=required_elements,
        speaker_notes=f"Explain this slide around the goal: {unit.goal}.",
        source_chunk_ids=chunk_ids,
        elements=elements,
    )
