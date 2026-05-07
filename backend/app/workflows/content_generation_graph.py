from functools import lru_cache
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.core.task import TaskStatus
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.assembler_node import assemble_content_spec
from app.workflows.nodes.element_flow_node import collect_unit_required_elements, dispatch_element_generation, dispatch_element_generation_node, merge_unit_elements
from app.workflows.nodes.finalizer_node import fail_task, finalize_task
from app.workflows.nodes.image_element_node import generate_image_element
from app.workflows.nodes.mindmap_element_node import generate_mindmap_element
from app.workflows.nodes.normalize_request_node import normalize_request
from app.workflows.nodes.planner_node import plan_outline
from app.workflows.nodes.renderer_node import (
    lecture_renderer,
    route_renderer,
    route_renderer_choice,
    slide_renderer,
)
from app.workflows.nodes.retriever_node import retrieve_for_planning, retrieve_for_unit
from app.workflows.nodes.unit_loop_node import (
    initialize_section_units,
    initialize_slide_units,
    merge_unit_result,
    route_content_type,
    route_content_type_choice,
    should_continue_units,
)
from app.workflows.nodes.unit_spec_generator_node import generate_unit_spec
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
    state = ContentGenerationState(
        request_id=request_id or f"task_{uuid4().hex[:12]}",
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        system_prompt=request.system_prompt,
        knowledge_base_ids=request.knowledge_base_ids,
        raw_request=request.model_dump(mode="json"),
        status=TaskStatus.running,
    )
    graph = build_content_generation_graph()
    result = graph.invoke(state)
    return ContentGenerationState.model_validate(result)


@lru_cache(maxsize=1)
def build_content_generation_graph():
    workflow = StateGraph(ContentGenerationState)

    workflow.add_node("normalize_request", normalize_request)
    workflow.add_node("retrieve_for_planning", retrieve_for_planning)
    workflow.add_node("plan_outline", plan_outline)
    workflow.add_node("validate_outline", validate_outline)
    workflow.add_node("route_content_type", route_content_type)
    workflow.add_node("initialize_section_units", initialize_section_units)
    workflow.add_node("initialize_slide_units", initialize_slide_units)
    workflow.add_node("retrieve_for_unit", retrieve_for_unit)
    workflow.add_node("generate_unit_spec", generate_unit_spec)
    workflow.add_node("validate_unit_spec", validate_unit_spec)
    workflow.add_node("collect_unit_required_elements", collect_unit_required_elements)
    workflow.add_node("dispatch_element_generation", dispatch_element_generation_node)
    workflow.add_node("generate_image_element", generate_image_element)
    workflow.add_node("generate_mindmap_element", generate_mindmap_element)
    workflow.add_node("merge_unit_elements", merge_unit_elements)
    workflow.add_node("validate_unit", validate_unit)
    workflow.add_node("merge_unit_result", merge_unit_result)
    workflow.add_node("assemble_content_spec", assemble_content_spec)
    workflow.add_node("validate_content", validate_content)
    workflow.add_node("route_renderer", route_renderer)
    workflow.add_node("lecture_renderer", lecture_renderer)
    workflow.add_node("slide_renderer", slide_renderer)
    workflow.add_node("finalize_task", finalize_task)
    workflow.add_node("fail_task", fail_task)

    workflow.add_edge(START, "normalize_request")
    workflow.add_edge("normalize_request", "retrieve_for_planning")
    workflow.add_edge("retrieve_for_planning", "plan_outline")
    workflow.add_edge("plan_outline", "validate_outline")
    workflow.add_conditional_edges(
        "validate_outline",
        route_after_outline_validation,
        {"pass": "route_content_type", "fail": "fail_task"},
    )
    workflow.add_conditional_edges(
        "route_content_type",
        route_content_type_choice,
        {"lecture": "initialize_section_units", "slide_deck": "initialize_slide_units"},
    )
    workflow.add_edge("initialize_section_units", "retrieve_for_unit")
    workflow.add_edge("initialize_slide_units", "retrieve_for_unit")
    workflow.add_edge("retrieve_for_unit", "generate_unit_spec")
    workflow.add_edge("generate_unit_spec", "validate_unit_spec")
    workflow.add_conditional_edges(
        "validate_unit_spec",
        route_after_unit_spec_validation,
        {"pass": "collect_unit_required_elements", "fail": "fail_task"},
    )
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
        {"pass": "merge_unit_result", "fail": "fail_task"},
    )
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
        {"lecture": "lecture_renderer", "slide_deck": "slide_renderer"},
    )
    workflow.add_edge("lecture_renderer", "finalize_task")
    workflow.add_edge("slide_renderer", "finalize_task")
    workflow.add_edge("finalize_task", END)
    workflow.add_edge("fail_task", END)

    return workflow.compile()


__all__ = [
    "run_content_generation",
    "build_content_generation_graph",
]
