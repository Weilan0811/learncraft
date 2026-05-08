from app.schemas.state import ContentGenerationState, UnitGenerationResult
from app.workflows.nodes.helpers import build_progress, current_outline_unit, ensure_monotonic_progress


def route_content_type(state: ContentGenerationState) -> dict[str, object]:
    return {"current_node": "route_content_type"}


def route_content_type_choice(state: ContentGenerationState) -> str:
    return state.content_type


def initialize_section_units(state: ContentGenerationState) -> dict[str, object]:
    return _initialize_units(state, current_node="initialize_section_units")


def initialize_slide_units(state: ContentGenerationState) -> dict[str, object]:
    return _initialize_units(state, current_node="initialize_slide_units")


def merge_unit_result(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    current_ids = {request.element_id for request in state.current_unit_element_requests}
    element_lookup = {element.id: element for element in state.elements if element.id in current_ids}
    unit_results = dict(state.unit_results)
    unit_results[unit.id] = UnitGenerationResult(
        unit_id=unit.id,
        status="completed",
        unit_spec=state.current_unit_spec,
        element_requests={request.element_id: request for request in state.current_unit_element_requests},
        elements=element_lookup,
        validation_report=state.validation_report,
    )
    completed = [*state.completed_unit_ids, unit.id]
    next_index = state.current_unit_index + 1
    next_unit_id = state.pending_unit_ids[next_index] if next_index < len(state.pending_unit_ids) else None
    return {
        "unit_results": unit_results,
        "completed_unit_ids": completed,
        "current_unit_index": next_index,
        "current_unit_id": next_unit_id,
        "current_node": "merge_unit_result",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(
                stage="unit_completed",
                current_node="merge_unit_result",
                current_unit_id=unit.id,
                completed_units=len(completed),
                total_units=len(state.pending_unit_ids),
            ),
        ),
    }


def should_continue_units(state: ContentGenerationState) -> str:
    if len(state.failed_unit_ids) > state.max_allowed_failed_units:
        return "failed"
    if state.current_unit_index < len(state.pending_unit_ids):
        return "continue"
    return "done"


def _initialize_units(state: ContentGenerationState, current_node: str) -> dict[str, object]:
    unit_ids = [unit.id for unit in state.outline.units] if state.outline else []
    return {
        "pending_unit_ids": unit_ids,
        "current_unit_index": 0,
        "completed_unit_ids": [],
        "failed_unit_ids": [],
        "current_unit_id": unit_ids[0] if unit_ids else None,
        "current_node": current_node,
        "progress": build_progress(
            stage="initializing_units",
            current_node=current_node,
            current_unit_id=unit_ids[0] if unit_ids else None,
            completed_units=0,
            total_units=len(unit_ids),
        ),
    }


__all__ = [
    "route_content_type",
    "route_content_type_choice",
    "initialize_section_units",
    "initialize_slide_units",
    "merge_unit_result",
    "should_continue_units",
]
