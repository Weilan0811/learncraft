from html import escape

from app.schemas.elements import ImageElement
from app.schemas.outline import OutlineUnit
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import ElementReferenceBlock, ElementRequest, LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.services.storage_service import LocalStorageService


SUPPORTED_WORKFLOW_ELEMENTS = {"image", "mindmap"}


def request_from_state(state: ContentGenerationState) -> ContentGenerationRequest:
    raw = state.raw_request or {}
    return ContentGenerationRequest(
        content_type=state.content_type,
        topic=state.topic,
        user_prompt=state.user_prompt,
        system_prompt=state.system_prompt,
        knowledge_base_ids=state.knowledge_base_ids,
        generation_options=raw.get("generation_options", {}),
        attachments=raw.get("attachments", []),
        kb_mode=raw.get("kb_mode", "platform"),
    )


def current_outline_unit(state: ContentGenerationState) -> OutlineUnit:
    if state.outline is None or not state.outline.units:
        raise ValueError("Outline units are required.")
    unit_id = state.current_unit_id or state.pending_unit_ids[state.current_unit_index]
    for unit in state.outline.units:
        if unit.id == unit_id:
            return unit
    raise ValueError(f"Current outline unit not found: {unit_id}")


def element_ref_ids(unit_spec) -> list[str]:
    from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
    if isinstance(unit_spec, InteractiveHtmlSectionSpec):
        return []
    if isinstance(unit_spec, LectureSection):
        return [block.element_id for block in unit_spec.blocks if isinstance(block, ElementReferenceBlock)]
    return [element.element_id for element in unit_spec.elements if element.type == "element_ref" and element.element_id]


def content_element_ref_ids(content_spec) -> list[str]:
    from app.schemas.specs.interactive_html import InteractiveHtmlSpec
    if isinstance(content_spec, InteractiveHtmlSpec):
        return []
    if isinstance(content_spec, LectureSpec):
        return [element_id for section in content_spec.sections for element_id in element_ref_ids(section)]
    return [element_id for slide in content_spec.slides for element_id in element_ref_ids(slide)]


def fallback_image_element(request: ElementRequest, reason: str, prompt: str | None = None) -> ImageElement:
    final_prompt = prompt or request.instruction
    try:
        svg = _fallback_svg(request.title, reason)
        record = LocalStorageService().save_bytes(
            asset_id=request.element_id,
            filename=f"{request.element_id}.svg",
            content=svg.encode("utf-8"),
            content_type="image/svg+xml",
            kind="image",
            metadata={"fallback": True, "reason": reason, "provider": "fallback", "format": "svg"},
        )
        asset_url = record.url
    except Exception:
        asset_url = "/api/assets/placeholder_image/download"
    return ImageElement(
        id=request.element_id,
        title=request.title,
        prompt=final_prompt,
        asset_url=asset_url,
        alt_text=f"{request.title} placeholder image",
        source_unit_id=request.source_unit_id,
        source_outline_unit_id=request.source_outline_unit_id,
        source_chunk_ids=request.source_chunk_ids,
        metadata={"fallback": True, "reason": reason, "prompt": final_prompt},
        generation_info={"generator": "image_generation_service", "fallback": True, "prompt": final_prompt},
    )


def build_progress(
    stage: str,
    current_node: str | None,
    current_unit_id: str | None = None,
    completed_units: int = 0,
    total_units: int = 0,
) -> dict[str, object]:
    percent = _percent_for_stage(stage, completed_units=completed_units, total_units=total_units)
    return {
        "stage": stage,
        "display_stage": _display_stage(stage),
        "current_stage": stage,
        "current_node": current_node,
        "current_unit_id": current_unit_id,
        "completed_units": completed_units,
        "total_units": total_units,
        "percent": percent,
    }


def ensure_monotonic_progress(previous: dict[str, object] | None, current: dict[str, object]) -> dict[str, object]:
    previous_percent = int((previous or {}).get("percent", 0) or 0)
    current_percent = int(current.get("percent", 0) or 0)
    return {**current, "percent": max(previous_percent, current_percent)}


def unit_progress(
    state: ContentGenerationState,
    current_stage: str,
    percent: int | None = None,
    current_node: str | None = None,
) -> dict[str, object]:
    progress = build_progress(
        stage=current_stage,
        current_node=current_node or state.current_node,
        current_unit_id=state.current_unit_id,
        completed_units=len(state.completed_unit_ids),
        total_units=len(state.pending_unit_ids),
    )
    if percent is not None:
        progress["percent"] = percent
    return ensure_monotonic_progress(state.progress, progress)


def _fallback_svg(title: str, reason: str) -> str:
    safe_title = escape(title)
    safe_reason = escape(reason)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">'
        '<rect width="1280" height="720" fill="#f8fafc"/>'
        '<rect x="80" y="80" width="1120" height="560" rx="24" fill="#e0f2fe" stroke="#0284c7" stroke-width="6"/>'
        f'<text x="120" y="230" font-family="Arial, sans-serif" font-size="54" font-weight="700" fill="#0f172a">{safe_title}</text>'
        f'<text x="120" y="320" font-family="Arial, sans-serif" font-size="28" fill="#334155">Fallback image: {safe_reason}</text>'
        '<circle cx="1040" cy="480" r="72" fill="#0f766e" opacity="0.9"/>'
        '<circle cx="950" cy="490" r="44" fill="#2563eb" opacity="0.9"/>'
        "</svg>"
    )


def _percent_for_stage(stage: str, completed_units: int = 0, total_units: int = 0) -> int:
    if stage in {"queued"}:
        return 0
    if stage in {"running", "normalizing"}:
        return 5
    if stage == "retrieving":
        return 15
    if stage in {"planning", "validating_outline"}:
        return 25
    if stage == "generating_direct_content":
        return 65
    if stage == "validating_direct_content":
        return 82
    if stage == "initializing_units":
        return 30
    if stage in {
        "retrieving_unit",
        "generating_unit",
        "validating_unit_spec",
        "collecting_elements",
        "generating_elements",
        "merging_elements",
        "validating_unit",
        "rendering_unit",
        "unit_render_ready",
        "unit_completed",
    }:
        if total_units <= 0:
            return 30
        unit_share = min(completed_units, total_units) / total_units
        return 30 + int(unit_share * 50)
    if stage in {"assembling_content", "validating_content"}:
        return 88
    if stage == "rendering":
        return 95
    if stage in {"completed", "failed"}:
        return 100
    return 5


def _display_stage(stage: str) -> str:
    labels = {
        "queued": "queued",
        "running": "running",
        "normalizing": "normalizing request",
        "retrieving": "retrieving knowledge",
        "planning": "planning outline",
        "generating_direct_content": "generating direct content",
        "validating_direct_content": "validating direct content",
        "validating_outline": "validating outline",
        "initializing_units": "initializing units",
        "retrieving_unit": "retrieving unit context",
        "generating_unit": "generating unit spec",
        "validating_unit_spec": "validating unit spec",
        "collecting_elements": "collecting elements",
        "generating_elements": "generating elements",
        "merging_elements": "merging elements",
        "validating_unit": "validating unit",
        "rendering_unit": "rendering unit",
        "unit_render_ready": "unit render ready",
        "unit_completed": "unit completed",
        "assembling_content": "assembling content",
        "validating_content": "validating content",
        "rendering": "rendering preview",
        "completed": "completed",
        "failed": "failed",
    }
    return labels.get(stage, stage)
