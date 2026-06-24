from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.schemas.elements import ContentElement
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot, TaskStreamEvent, UnitGenerationResult, WorkflowError
from app.workflows.nodes.element_flow_node import collect_unit_required_elements, merge_unit_elements
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress
from app.workflows.nodes.image_element_node import generate_image_element
from app.workflows.nodes.mindmap_element_node import generate_mindmap_element
from app.workflows.nodes.publish_event_node import publish_unit_render
from app.workflows.nodes.render_unit_repair_node import fallback_render_unit, repair_render_unit
from app.workflows.nodes.retriever_node import retrieve_for_unit
from app.workflows.nodes.unit_loop_node import merge_unit_result
from app.workflows.nodes.unit_renderer_node import _build_partial_render_model, render_unit, route_after_render_unit
from app.workflows.nodes.unit_spec_generator_node import generate_unit_spec
from app.workflows.nodes.unit_spec_repair_node import fallback_unit_spec, repair_unit_spec
from app.workflows.nodes.validator_node import (
    route_after_unit_spec_validation,
    route_after_unit_validation,
    validate_unit,
    validate_unit_spec,
)


@dataclass
class UnitPipelineResult:
    unit_id: str
    unit_result: UnitGenerationResult | None = None
    render_unit: RenderUnitSnapshot | None = None
    context: list[object] = field(default_factory=list)
    elements: list[ContentElement] = field(default_factory=list)
    element_status: dict[str, object] = field(default_factory=dict)
    stream_events: list[TaskStreamEvent] = field(default_factory=list)
    retry_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    workflow_errors: list[WorkflowError] = field(default_factory=list)
    failed: bool = False


def build_unit_batches(unit_ids: list[str], concurrency: int) -> list[list[str]]:
    batch_size = max(1, concurrency)
    return [unit_ids[index : index + batch_size] for index in range(0, len(unit_ids), batch_size)]


def generate_units_parallel(state: ContentGenerationState, concurrency: int | None = None) -> dict[str, object]:
    unit_ids = list(state.pending_unit_ids)
    if not unit_ids:
        return {
            "current_node": "generate_units_parallel",
            "progress": build_progress(
                stage="unit_completed",
                current_node="generate_units_parallel",
                completed_units=0,
                total_units=0,
            ),
        }
    settings = get_settings()
    max_workers = max(1, concurrency if concurrency is not None else int(getattr(settings, "generation_unit_concurrency", 3)))
    results_by_unit: dict[str, UnitPipelineResult] = {}

    for batch in build_unit_batches(unit_ids, max_workers):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_unit_pipeline, state, unit_id): unit_id for unit_id in batch}
            for future in as_completed(futures):
                unit_id = futures[future]
                try:
                    results_by_unit[unit_id] = future.result()
                except Exception as exc:
                    results_by_unit[unit_id] = UnitPipelineResult(unit_id=unit_id, failed=True, errors=[f"unit pipeline failed: {exc}"])

    ordered_results = [results_by_unit[unit_id] for unit_id in unit_ids if unit_id in results_by_unit]
    completed_unit_ids = [result.unit_id for result in ordered_results if not result.failed and result.unit_result is not None]
    failed_unit_ids = [result.unit_id for result in ordered_results if result.failed or result.unit_result is None]

    unit_results = dict(state.unit_results)
    unit_context_map = dict(state.unit_context_map)
    render_units = dict(state.render_units)
    element_status = dict(state.element_status)
    stream_events = list(state.stream_events)
    retry_counts = dict(state.retry_counts)
    errors = list(state.errors)
    workflow_errors = list(state.workflow_errors)
    elements_by_id = {element.id: element for element in state.elements}

    for result in ordered_results:
        if result.context:
            unit_context_map[result.unit_id] = result.context  # type: ignore[assignment]
        if result.unit_result is not None:
            unit_results[result.unit_id] = result.unit_result
        if result.render_unit is not None:
            render_units[result.unit_id] = result.render_unit
        for element in result.elements:
            elements_by_id[element.id] = element
        element_status.update(result.element_status)
        stream_events.extend(result.stream_events)
        retry_counts.update(result.retry_counts)
        errors.extend(result.errors)
        workflow_errors.extend(result.workflow_errors)

    partial_render_model = _build_partial_render_model(state, render_units) if render_units else state.partial_render_model
    progress = ensure_monotonic_progress(
        state.progress,
        build_progress(
            stage="unit_completed",
            current_node="generate_units_parallel",
            completed_units=len(completed_unit_ids),
            total_units=len(unit_ids),
        ),
    )
    next_index = len(completed_unit_ids) + len(failed_unit_ids)
    return {
        "unit_context_map": unit_context_map,
        "unit_results": unit_results,
        "render_units": render_units,
        "partial_render_model": partial_render_model,
        "elements": list(elements_by_id.values()),
        "element_status": element_status,
        "stream_events": stream_events,
        "completed_unit_ids": completed_unit_ids,
        "failed_unit_ids": failed_unit_ids,
        "current_unit_index": next_index,
        "current_unit_id": None,
        "current_unit_context": [],
        "current_unit_spec": None,
        "current_unit_element_requests": [],
        "current_unit_elements": [],
        "retry_counts": retry_counts,
        "errors": errors,
        "workflow_errors": workflow_errors,
        "current_node": "generate_units_parallel",
        "progress": progress,
    }


def process_unit_pipeline(state: ContentGenerationState, unit_id: str) -> UnitPipelineResult:
    unit_index = state.pending_unit_ids.index(unit_id) if unit_id in state.pending_unit_ids else 0
    local = state.model_copy(
        deep=True,
        update={
            "current_unit_id": unit_id,
            "current_unit_index": unit_index,
            "current_unit_context": [],
            "current_unit_spec": None,
            "current_unit_element_requests": [],
            "current_unit_elements": [],
        },
    )
    start_errors = list(local.errors)
    start_workflow_error_count = len(local.workflow_errors)
    start_event_count = len(local.stream_events)

    try:
        local = _apply_update(local, retrieve_for_unit(local))
        local = _apply_update(local, generate_unit_spec(local))
        local = _validate_or_recover_unit_spec(local)
        local = _apply_update(local, collect_unit_required_elements(local))
        local = _generate_current_unit_elements(local)
        local = _apply_update(local, merge_unit_elements(local))
        local = _apply_update(local, validate_unit(local))
        if route_after_unit_validation(local) != "pass":
            return _failed_result(local, unit_id, start_errors, start_workflow_error_count, start_event_count)
        local = _render_or_recover_unit(local)
        local = _apply_update(local, publish_unit_render(local))
        local = _apply_update(local, merge_unit_result(local))
    except Exception as exc:
        return UnitPipelineResult(unit_id=unit_id, failed=True, errors=[f"unit pipeline failed: {exc}"])

    unit_result = local.unit_results.get(unit_id)
    return UnitPipelineResult(
        unit_id=unit_id,
        unit_result=unit_result,
        render_unit=local.render_units.get(unit_id),
        context=list(local.current_unit_context),
        elements=[element for element in local.elements if _element_belongs_to_unit(element, unit_id)],
        element_status={key: value for key, value in local.element_status.items() if _element_status_belongs_to_unit(key, unit_result)},
        stream_events=list(local.stream_events[start_event_count:]),
        retry_counts={key: value for key, value in local.retry_counts.items() if unit_id in key},
        errors=[error for error in local.errors if error not in start_errors],
        workflow_errors=list(local.workflow_errors[start_workflow_error_count:]),
        failed=unit_result is None,
    )


def _validate_or_recover_unit_spec(local: ContentGenerationState) -> ContentGenerationState:
    local = _apply_update(local, validate_unit_spec(local))
    route = route_after_unit_spec_validation(local)
    if route == "pass":
        return local
    if route == "repair":
        local = _apply_update(local, repair_unit_spec(local))
        local = _apply_update(local, validate_unit_spec(local))
        route = route_after_unit_spec_validation(local)
    if route == "fallback":
        local = _apply_update(local, fallback_unit_spec(local))
        local = _apply_update(local, validate_unit_spec(local))
        route = route_after_unit_spec_validation(local)
    if route != "pass":
        raise RuntimeError("; ".join(str(error) for error in (local.spec_validation_report or {}).get("errors", [])) or "unit spec validation failed")
    return local


def _generate_current_unit_elements(local: ContentGenerationState) -> ContentGenerationState:
    generated = []
    for request in local.current_unit_element_requests:
        if request.type == "image":
            update = generate_image_element({"element_request": request})
        elif request.type == "mindmap":
            update = generate_mindmap_element({"element_request": request})
        else:
            continue
        generated.extend(update.get("current_unit_elements", []))
    return local.model_copy(update={"current_unit_elements": generated})


def _render_or_recover_unit(local: ContentGenerationState) -> ContentGenerationState:
    local = _apply_update(local, render_unit(local))
    route = route_after_render_unit(local)
    while route != "pass":
        if route == "retry":
            local = _apply_update(local, render_unit(local))
        elif route == "repair":
            local = _apply_update(local, repair_render_unit(local))
        elif route == "fallback":
            local = _apply_update(local, fallback_render_unit(local))
        else:
            raise RuntimeError("; ".join(local.errors) or "unit render failed")
        route = route_after_render_unit(local)
    return local


def _failed_result(
    local: ContentGenerationState,
    unit_id: str,
    start_errors: list[str],
    start_workflow_error_count: int,
    start_event_count: int,
) -> UnitPipelineResult:
    return UnitPipelineResult(
        unit_id=unit_id,
        failed=True,
        errors=[error for error in local.errors if error not in start_errors],
        workflow_errors=list(local.workflow_errors[start_workflow_error_count:]),
        stream_events=list(local.stream_events[start_event_count:]),
        retry_counts={key: value for key, value in local.retry_counts.items() if unit_id in key},
    )


def _apply_update(state: ContentGenerationState, update: dict[str, object]) -> ContentGenerationState:
    return state.model_copy(update=update)


def _element_belongs_to_unit(element: ContentElement, unit_id: str) -> bool:
    return element.source_unit_id == unit_id or element.source_outline_unit_id == unit_id


def _element_status_belongs_to_unit(element_id: str, unit_result: UnitGenerationResult | None) -> bool:
    return bool(unit_result and element_id in unit_result.element_requests)


__all__ = [
    "UnitPipelineResult",
    "build_unit_batches",
    "generate_units_parallel",
    "process_unit_pipeline",
]
