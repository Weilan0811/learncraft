from app.schemas.elements import ImageElement
from app.schemas.outline import OutlineUnit
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import ElementReferenceBlock, ElementRequest, LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.state import ContentGenerationState


SUPPORTED_WORKFLOW_ELEMENTS = {"image", "mindmap"}


def request_from_state(state: ContentGenerationState) -> ContentGenerationRequest:
    return ContentGenerationRequest(
        content_type=state.content_type,
        topic=state.topic,
        user_prompt=state.user_prompt,
        system_prompt=state.system_prompt,
        knowledge_base_ids=state.knowledge_base_ids,
        generation_options=(state.raw_request or {}).get("generation_options", {}),
    )


def current_outline_unit(state: ContentGenerationState) -> OutlineUnit:
    if state.outline is None or not state.outline.units:
        raise ValueError("Outline units are required.")
    unit_id = state.current_unit_id or state.pending_unit_ids[state.current_unit_index]
    for unit in state.outline.units:
        if unit.id == unit_id:
            return unit
    raise ValueError(f"Current outline unit not found: {unit_id}")


def element_ref_ids(unit_spec: LectureSection | SlideSpecPage) -> list[str]:
    if isinstance(unit_spec, LectureSection):
        return [block.element_id for block in unit_spec.blocks if isinstance(block, ElementReferenceBlock)]
    return [element.element_id for element in unit_spec.elements if element.type == "element_ref" and element.element_id]


def content_element_ref_ids(content_spec: LectureSpec | SlideDeckSpec) -> list[str]:
    if isinstance(content_spec, LectureSpec):
        return [element_id for section in content_spec.sections for element_id in element_ref_ids(section)]
    return [element_id for slide in content_spec.slides for element_id in element_ref_ids(slide)]


def fallback_image_element(request: ElementRequest, reason: str) -> ImageElement:
    return ImageElement(
        id=request.element_id,
        title=request.title,
        prompt=request.instruction,
        asset_url="/api/assets/placeholder_image/download",
        alt_text=f"{request.title} 占位图",
        source_unit_id=request.source_unit_id,
        source_outline_unit_id=request.source_outline_unit_id,
        source_chunk_ids=request.source_chunk_ids,
        metadata={"fallback": True, "reason": reason},
        generation_info={"generator": "image_generation_service", "fallback": True},
    )


def unit_progress(state: ContentGenerationState, current_stage: str, percent: int) -> dict[str, object]:
    return {
        "current_stage": current_stage,
        "current_unit_id": state.current_unit_id,
        "completed_units": len(state.completed_unit_ids),
        "total_units": len(state.pending_unit_ids),
        "percent": percent,
    }
