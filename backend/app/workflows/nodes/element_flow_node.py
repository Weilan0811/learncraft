from langgraph.types import Send

from app.schemas.specs import ElementRequest
from app.schemas.state import ContentGenerationState, ElementStatus
from app.workflows.nodes.helpers import SUPPORTED_WORKFLOW_ELEMENTS, current_outline_unit, unit_progress


def collect_unit_required_elements(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    unit_spec = state.current_unit_spec
    requests: list[ElementRequest] = []
    if unit_spec is not None:
        for required in unit_spec.required_elements:
            requests.append(
                ElementRequest(
                    element_id=required.element_id,
                    type=required.type,
                    title=required.title,
                    purpose=required.purpose,
                    instruction=required.instruction,
                    source_content_type=state.content_type,
                    source_unit_id=required.source_unit_id,
                    source_outline_unit_id=required.source_outline_unit_id,
                    source_chunk_ids=required.source_chunk_ids,
                    context={
                        "unit_title": unit.title,
                        "core_message": unit.core_message,
                        "key_points": unit.key_points,
                    },
                    constraints={
                        "language": (state.normalized_request or {}).get("language", "zh-CN"),
                        "style": required.style or (state.normalized_request or {}).get("style", "educational"),
                        "aspect_ratio": required.aspect_ratio or "16:9",
                    },
                    render_hints={"usage": "unit_content"},
                    priority=required.priority,
                )
            )
    element_status = dict(state.element_status)
    for request in requests:
        element_status[request.element_id] = ElementStatus(element_id=request.element_id, type=request.type)
    return {
        "current_unit_element_requests": requests,
        "element_status": element_status,
        "current_node": "collect_unit_required_elements",
        "progress": unit_progress(state, "collecting_elements", 65),
    }


def dispatch_element_generation_node(state: ContentGenerationState) -> dict[str, object]:
    return {"current_node": "dispatch_element_generation"}


def dispatch_element_generation(state: ContentGenerationState):
    sends: list[Send] = []
    for request in state.current_unit_element_requests:
        if request.type == "image":
            sends.append(Send("generate_image_element", {"element_request": request}))
        elif request.type == "mindmap":
            sends.append(Send("generate_mindmap_element", {"element_request": request}))
    return sends or "merge"


def merge_unit_elements(state: ContentGenerationState) -> dict[str, object]:
    merged = {element.id: element for element in state.elements}
    current_ids = {request.element_id for request in state.current_unit_element_requests}
    current_elements = [element for element in state.current_unit_elements if element.id in current_ids]
    for element in current_elements:
        merged[element.id] = element
    element_status = dict(state.element_status)
    for element in current_elements:
        if element.type in SUPPORTED_WORKFLOW_ELEMENTS:
            element_status[element.id] = ElementStatus(element_id=element.id, type=element.type, status=element.status)
    return {
        "elements": list(merged.values()),
        "element_status": element_status,
        "current_node": "merge_unit_elements",
        "progress": unit_progress(state, "merging_elements", 75),
    }


__all__ = [
    "collect_unit_required_elements",
    "dispatch_element_generation_node",
    "dispatch_element_generation",
    "merge_unit_elements",
]
