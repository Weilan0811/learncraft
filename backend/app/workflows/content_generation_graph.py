from functools import lru_cache
from datetime import UTC, datetime
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.core.debug_artifacts import WorkflowDebugArtifacts
from app.core.logging import append_workflow_log
from app.core.task import TaskStatus
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState, TaskStreamEvent
from app.workflows.nodes.helpers import build_progress
from app.workflows.nodes.assembler_node import assemble_content_spec
from app.workflows.nodes.element_flow_node import collect_unit_required_elements, dispatch_element_generation, dispatch_element_generation_node, merge_unit_elements
from app.workflows.nodes.finalizer_node import fail_task, finalize_task
from app.workflows.nodes.direct_content_node import (
    generate_direct_content,
    render_direct_content,
    route_after_direct_validation,
    validate_direct_content,
)
from app.workflows.nodes.generation_mode_node import route_generation_mode, route_generation_mode_choice
from app.workflows.nodes.image_element_node import generate_image_element
from app.workflows.nodes.mindmap_element_node import generate_mindmap_element
from app.workflows.nodes.normalize_request_node import normalize_request
from app.workflows.nodes.planner_node import plan_outline
from app.workflows.nodes.publish_event_node import publish_unit_render
from app.workflows.nodes.renderer_node import (
    interactive_html_renderer,
    lecture_renderer,
    route_renderer,
    route_renderer_choice,
    slide_renderer,
)
from app.workflows.nodes.render_unit_repair_node import fallback_render_unit, repair_render_unit
from app.workflows.nodes.retriever_node import retrieve_for_planning, retrieve_for_unit
from app.workflows.nodes.unit_spec_repair_node import fallback_unit_spec, repair_unit_spec
from app.workflows.nodes.unit_loop_node import (
    initialize_interactive_html_units,
    initialize_section_units,
    initialize_slide_units,
    merge_unit_result,
    route_content_type,
    route_content_type_choice,
    should_continue_units,
)
from app.workflows.nodes.unit_spec_generator_node import generate_unit_spec
from app.workflows.nodes.unit_renderer_node import render_unit
from app.workflows.nodes.unit_renderer_node import route_after_render_unit
from app.workflows.nodes.validator_node import (
    route_after_content_validation,
    route_after_outline_validation,
    route_after_unit_spec_validation,
    route_after_unit_validation,
    validate_content,
    validate_outline,
    validate_unit,
    validate_unit_spec,
)


def run_content_generation(
    request: ContentGenerationRequest,
    request_id: str | None = None,
) -> ContentGenerationState:
    """Run the synchronous MVP content-generation graph."""
    final_update = None
    for final_update in stream_content_generation(request, request_id=request_id):
        pass
    if final_update is None:
        raise RuntimeError("content generation produced no state updates")
    return ContentGenerationState.model_validate(final_update)


def stream_content_generation(
    request: ContentGenerationRequest,
    request_id: str | None = None,
):
    """Stream the content-generation graph execution, yielding updates after each node."""
    state = ContentGenerationState(
        request_id=request_id or f"task_{uuid4().hex[:12]}",
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        system_prompt=request.system_prompt,
        knowledge_base_ids=request.knowledge_base_ids,
        raw_request=request.model_dump(mode="json"),
        status=TaskStatus.running,
        progress=build_progress(stage="running", current_node="run_content_generation"),
    )
    graph = build_content_generation_graph()
    debug_artifacts = WorkflowDebugArtifacts(state.request_id)
    debug_step_paths: dict[str, str] = {}

    current = state.model_dump(mode="python")
    current["stream_events"] = [
        TaskStreamEvent(
            event_id=f"event_{uuid4().hex[:12]}",
            task_id=state.request_id,
            type="task_started",
            payload={"topic": state.topic},
            created_at=datetime.now(UTC).isoformat(),
        ).model_dump(mode="python")
    ]
    current["logs"] = append_workflow_log(
        [],
        task_id=state.request_id,
        content_type=state.content_type,
        event="task_started",
        message="Content generation task started.",
        node="run_content_generation",
        detail={"topic": state.topic, "knowledge_base_ids": state.knowledge_base_ids},
    )
    yield current

    for event_type, payload in graph.stream(state, stream_mode=["updates", "values"]):
        if event_type == "updates":
            for node_name, node_output in payload.items():
                debug_step_paths[str(node_name)] = debug_artifacts.write_step(str(node_name), node_output)
            continue
        if event_type != "values":
            continue
        event = payload
        previous_logs = current.get("logs", [])
        previous_stream_events = current.get("stream_events", [])
        current.update(event)
        if not current.get("logs"):
            current["logs"] = previous_logs
        if event.get("stream_events") and previous_stream_events:
            current["stream_events"] = _merge_stream_events(previous_stream_events, current.get("stream_events", []))
        elif not current.get("stream_events"):
            current["stream_events"] = previous_stream_events
        if current.get("progress") is None:
            current["progress"] = build_progress(
                stage=str(current.get("status", TaskStatus.running)),
                current_node=current.get("current_node"),
            )
        current = _append_stream_log(current, debug_artifact_path=debug_step_paths.get(str(current.get("current_node"))))
        debug_artifacts.write_state_artifacts(current)
        yield current


def _append_stream_log(current: dict[str, object], debug_artifact_path: str | None = None) -> dict[str, object]:
    node = current.get("current_node")
    status = current.get("status")
    status_value = getattr(status, "value", status)
    logs = [dict(entry) for entry in current.get("logs", [])]
    current["logs"] = append_workflow_log(
        logs,
        task_id=str(current.get("request_id")),
        content_type=str(current.get("content_type")),
        event="node_completed",
        message=f"Workflow node completed: {node or 'unknown'}.",
        level="info",
        node=str(node) if node else None,
        unit_id=str(current.get("current_unit_id")) if current.get("current_unit_id") else None,
        detail={
            "status": str(status_value),
            "progress": current.get("progress") or {},
            "errors": current.get("errors") or [],
            "workflow_errors": current.get("workflow_errors") or [],
            **({"debug_artifact_path": debug_artifact_path} if debug_artifact_path else {}),
        },
    )
    if status_value in {TaskStatus.completed, TaskStatus.failed}:
        terminal_event = "task_completed" if status_value == TaskStatus.completed else "task_failed"
        current["logs"] = append_workflow_log(
            [dict(entry) for entry in current.get("logs", [])],
            task_id=str(current.get("request_id")),
            content_type=str(current.get("content_type")),
            event=terminal_event,
            message="Content generation task completed." if terminal_event == "task_completed" else "Content generation task failed.",
            level="error" if terminal_event == "task_failed" else "info",
            node=str(node) if node else None,
            unit_id=str(current.get("current_unit_id")) if current.get("current_unit_id") else None,
            detail={
                "status": str(status_value),
                "progress": current.get("progress") or {},
                "errors": current.get("errors") or [],
            },
        )
    return current


def _merge_stream_events(existing: object, incoming: object) -> list[object]:
    merged: list[object] = []
    seen: set[str] = set()
    for event in [*list(existing or []), *list(incoming or [])]:
        event_id = event.get("event_id") if isinstance(event, dict) else getattr(event, "event_id", None)
        key = str(event_id or len(merged))
        if key in seen:
            continue
        seen.add(key)
        merged.append(event)
    return merged


@lru_cache(maxsize=1)
def build_content_generation_graph():
    workflow = StateGraph(ContentGenerationState)

    workflow.add_node("normalize_request", normalize_request)
    workflow.add_node("retrieve_for_planning", retrieve_for_planning)
    workflow.add_node("route_generation_mode", route_generation_mode)
    workflow.add_node("generate_direct_content", generate_direct_content)
    workflow.add_node("validate_direct_content", validate_direct_content)
    workflow.add_node("render_direct_content", render_direct_content)
    workflow.add_node("plan_outline", plan_outline)
    workflow.add_node("validate_outline", validate_outline)
    workflow.add_node("route_content_type", route_content_type)
    workflow.add_node("initialize_section_units", initialize_section_units)
    workflow.add_node("initialize_slide_units", initialize_slide_units)
    workflow.add_node("initialize_interactive_html_units", initialize_interactive_html_units)
    workflow.add_node("retrieve_for_unit", retrieve_for_unit)
    workflow.add_node("generate_unit_spec", generate_unit_spec)
    workflow.add_node("validate_unit_spec", validate_unit_spec)
    workflow.add_node("repair_unit_spec", repair_unit_spec)
    workflow.add_node("fallback_unit_spec", fallback_unit_spec)
    workflow.add_node("collect_unit_required_elements", collect_unit_required_elements)
    workflow.add_node("dispatch_element_generation", dispatch_element_generation_node)
    workflow.add_node("generate_image_element", generate_image_element)
    workflow.add_node("generate_mindmap_element", generate_mindmap_element)
    workflow.add_node("merge_unit_elements", merge_unit_elements)
    workflow.add_node("validate_unit", validate_unit)
    workflow.add_node("render_unit", render_unit)
    workflow.add_node("repair_render_unit", repair_render_unit)
    workflow.add_node("fallback_render_unit", fallback_render_unit)
    workflow.add_node("publish_unit_render", publish_unit_render)
    workflow.add_node("merge_unit_result", merge_unit_result)
    workflow.add_node("assemble_content_spec", assemble_content_spec)
    workflow.add_node("validate_content", validate_content)
    workflow.add_node("route_renderer", route_renderer)
    workflow.add_node("lecture_renderer", lecture_renderer)
    workflow.add_node("slide_renderer", slide_renderer)
    workflow.add_node("interactive_html_renderer", interactive_html_renderer)
    workflow.add_node("finalize_task", finalize_task)
    workflow.add_node("fail_task", fail_task)

    workflow.add_edge(START, "normalize_request")
    workflow.add_edge("normalize_request", "retrieve_for_planning")
    workflow.add_edge("retrieve_for_planning", "route_generation_mode")
    workflow.add_conditional_edges(
        "route_generation_mode",
        route_generation_mode_choice,
        {"unit_loop": "plan_outline", "direct": "generate_direct_content"},
    )
    workflow.add_edge("generate_direct_content", "validate_direct_content")
    workflow.add_conditional_edges(
        "validate_direct_content",
        route_after_direct_validation,
        {"pass": "render_direct_content", "fail": "fail_task"},
    )
    workflow.add_edge("render_direct_content", "finalize_task")
    workflow.add_edge("plan_outline", "validate_outline")
    workflow.add_conditional_edges(
        "validate_outline",
        route_after_outline_validation,
        {"pass": "route_content_type", "fail": "fail_task"},
    )
    workflow.add_conditional_edges(
        "route_content_type",
        route_content_type_choice,
        {"lecture": "initialize_section_units", "slide_deck": "initialize_slide_units", "interactive_html": "initialize_interactive_html_units"},
    )
    workflow.add_edge("initialize_section_units", "retrieve_for_unit")
    workflow.add_edge("initialize_slide_units", "retrieve_for_unit")
    workflow.add_edge("initialize_interactive_html_units", "retrieve_for_unit")
    workflow.add_edge("retrieve_for_unit", "generate_unit_spec")
    workflow.add_edge("generate_unit_spec", "validate_unit_spec")
    workflow.add_conditional_edges(
        "validate_unit_spec",
        route_after_unit_spec_validation,
        {"pass": "collect_unit_required_elements", "repair": "repair_unit_spec", "fallback": "fallback_unit_spec", "fail": "fail_task"},
    )
    workflow.add_edge("repair_unit_spec", "validate_unit_spec")
    workflow.add_edge("fallback_unit_spec", "validate_unit_spec")
    workflow.add_edge("collect_unit_required_elements", "dispatch_element_generation")
    workflow.add_conditional_edges(
        "dispatch_element_generation",
        dispatch_element_generation,
        {"merge": "merge_unit_elements"},
    )
    workflow.add_edge("generate_image_element", "merge_unit_elements")
    workflow.add_edge("generate_mindmap_element", "merge_unit_elements")
    workflow.add_edge("merge_unit_elements", "validate_unit")
    workflow.add_conditional_edges(
        "validate_unit",
        route_after_unit_validation,
        {"pass": "render_unit", "fail": "fail_task"},
    )
    workflow.add_conditional_edges(
        "render_unit",
        route_after_render_unit,
        {"pass": "publish_unit_render", "retry": "render_unit", "repair": "repair_render_unit", "fallback": "fallback_render_unit", "fail": "fail_task"},
    )
    workflow.add_conditional_edges(
        "repair_render_unit",
        route_after_render_unit,
        {"pass": "publish_unit_render", "retry": "render_unit", "repair": "repair_render_unit", "fallback": "fallback_render_unit", "fail": "fail_task"},
    )
    workflow.add_edge("fallback_render_unit", "publish_unit_render")
    workflow.add_edge("publish_unit_render", "merge_unit_result")
    workflow.add_conditional_edges(
        "merge_unit_result",
        should_continue_units,
        {"continue": "retrieve_for_unit", "done": "assemble_content_spec", "failed": "fail_task"},
    )
    workflow.add_edge("assemble_content_spec", "validate_content")
    workflow.add_conditional_edges(
        "validate_content",
        route_after_content_validation,
        {"pass": "route_renderer", "fail": "fail_task"},
    )
    workflow.add_conditional_edges(
        "route_renderer",
        route_renderer_choice,
        {"lecture": "lecture_renderer", "slide_deck": "slide_renderer", "interactive_html": "interactive_html_renderer"},
    )
    workflow.add_edge("lecture_renderer", "finalize_task")
    workflow.add_edge("slide_renderer", "finalize_task")
    workflow.add_edge("interactive_html_renderer", "finalize_task")
    workflow.add_edge("finalize_task", END)
    workflow.add_edge("fail_task", END)

    return workflow.compile()


__all__ = [
    "run_content_generation",
    "stream_content_generation",
    "build_content_generation_graph",
]
