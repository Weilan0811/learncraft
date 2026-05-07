from app.workflows.content_generation_graph import build_content_generation_graph, run_content_generation
from app.workflows.nodes.assembler_node import assemble_content_spec
from app.workflows.nodes.element_flow_node import collect_unit_required_elements, dispatch_element_generation, merge_unit_elements
from app.workflows.nodes.finalizer_node import fail_task, finalize_task
from app.workflows.nodes.image_element_node import generate_image_element
from app.workflows.nodes.mindmap_element_node import generate_mindmap_element
from app.workflows.nodes.planner_node import plan_outline
from app.workflows.nodes.renderer_node import lecture_renderer, slide_renderer
from app.workflows.nodes.retriever_node import retrieve_for_planning, retrieve_for_unit
from app.workflows.nodes.unit_loop_node import initialize_section_units, initialize_slide_units, merge_unit_result
from app.workflows.nodes.unit_spec_generator_node import generate_unit_spec
from app.workflows.nodes.validator_node import validate_content, validate_outline, validate_unit, validate_unit_spec


def test_workflow_nodes_are_importable_from_focused_modules() -> None:
    nodes = [
        assemble_content_spec,
        collect_unit_required_elements,
        dispatch_element_generation,
        merge_unit_elements,
        fail_task,
        finalize_task,
        generate_image_element,
        generate_mindmap_element,
        plan_outline,
        lecture_renderer,
        slide_renderer,
        retrieve_for_planning,
        retrieve_for_unit,
        initialize_section_units,
        initialize_slide_units,
        merge_unit_result,
        generate_unit_spec,
        validate_content,
        validate_outline,
        validate_unit,
        validate_unit_spec,
    ]

    assert all(callable(node) for node in nodes)


def test_content_generation_graph_exports_public_entrypoints_only() -> None:
    assert callable(run_content_generation)
    assert callable(build_content_generation_graph)


def test_legacy_node_shims_are_removed() -> None:
    import importlib.util

    removed_modules = [
        "app.workflows.nodes.element_collector_node",
        "app.workflows.nodes.element_dispatcher_node",
        "app.workflows.nodes.element_merger_node",
        "app.workflows.nodes.exporter_node",
        "app.workflows.nodes.generator_node",
        "app.workflows.nodes.unit_initializer_node",
        "app.workflows.nodes.unit_result_node",
    ]

    assert all(importlib.util.find_spec(module_name) is None for module_name in removed_modules)
