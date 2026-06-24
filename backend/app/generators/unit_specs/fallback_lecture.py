from app.generators.unit_specs.element_requirements import image_spec_for_unit, mindmap_spec_for_unit
from app.schemas.outline import OutlineUnit
from app.schemas.specs import ElementReferenceBlock, LectureSection, RequiredElementSpec, TextBlock
from app.schemas.state import ContentGenerationState


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
        image_spec = image_spec_for_unit(
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
        mindmap_spec = mindmap_spec_for_unit(
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
