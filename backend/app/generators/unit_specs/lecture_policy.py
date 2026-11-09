from app.generators.unit_specs.element_requirements import image_spec_for_unit
from app.schemas.outline import OutlineUnit
from app.schemas.specs import ElementReferenceBlock, LectureSection, RequiredElementSpec
from app.schemas.state import ContentGenerationState

LECTURE_IMAGE_ASPECT_RATIO = "4:3"
LECTURE_IMAGE_DEFAULT_STYLE = "clean educational illustration"
LECTURE_IMAGE_PURPOSE = "Use a focused visual to make the section's core concept easier to understand."


def build_lecture_image_spec(
    unit: OutlineUnit,
    unit_spec_id: str,
    request_id: str,
    chunk_ids: list[str],
    style: str | None = None,
) -> RequiredElementSpec:
    """Lecture-owned default image spec; the generic builder stays type-agnostic."""
    return image_spec_for_unit(
        unit=unit,
        unit_spec_id=unit_spec_id,
        request_id=request_id,
        chunk_ids=chunk_ids,
        aspect_ratio=LECTURE_IMAGE_ASPECT_RATIO,
        style=style or LECTURE_IMAGE_DEFAULT_STYLE,
        purpose=LECTURE_IMAGE_PURPOSE,
        instruction=(
            f"Create a local illustration asset for '{unit.title}', meant to be embedded inside a lecture section. "
            f"Show the core message: {unit.core_message}. Use a focused diagram, timeline, process graphic, or "
            "concept illustration with a clear hierarchy and concise labels. Do not create a full presentation slide, "
            "slide title, banner, footer, agenda, summary panel, or page-like teaching layout. Avoid decorative "
            "backgrounds, tiny text, unrelated people, and vague stock imagery."
        ),
    )


def enforce_single_lecture_image(
    section: LectureSection,
    state: ContentGenerationState,
    unit: OutlineUnit,
    chunk_ids: list[str],
) -> LectureSection:
    """Keep exactly one image per lecture section; drop other element types."""
    options = state.normalized_request or {}
    image_elements = [item for item in section.required_elements if item.type == "image"][:1]
    if image_elements:
        image_spec = image_elements[0]
    else:
        image_spec = build_lecture_image_spec(
            unit=unit,
            unit_spec_id=section.id,
            request_id=state.request_id,
            chunk_ids=chunk_ids,
            style=str(options["image_style"]) if options.get("image_style") else None,
        )

    kept_element_id = image_spec.element_id
    blocks = [
        block
        for block in section.blocks
        if not (isinstance(block, ElementReferenceBlock) and block.element_id != kept_element_id)
    ]
    if not any(isinstance(block, ElementReferenceBlock) and block.element_id == kept_element_id for block in blocks):
        blocks.append(
            ElementReferenceBlock(
                id=f"{section.id}_image_ref",
                title=image_spec.title,
                element_id=kept_element_id,
            )
        )

    return section.model_copy(update={"required_elements": [image_spec], "blocks": blocks})
