from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import LectureSpec, SlideDeckSpec
from app.workflows.content_generation_graph import run_content_generation


def test_langgraph_workflow_populates_lecture_unit_state() -> None:
    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="人工智能基础导论",
            user_prompt="生成一份讲义",
        )
    )

    assert state.status == "completed"
    assert state.outline is not None
    assert state.outline.units
    assert state.pending_unit_ids == [unit.id for unit in state.outline.units]
    assert state.completed_unit_ids == state.pending_unit_ids
    assert state.unit_results
    assert state.content_spec is not None
    assert isinstance(state.content_spec, LectureSpec)
    assert state.content_spec.sections[0].outline_unit_id == state.outline.units[0].id
    assert state.content_spec.sections[0].required_elements
    assert state.elements
    assert {element.type for element in state.elements} == {"image", "mindmap"}
    assert state.render_model is not None
    assert state.current_node == "finalize_task"
    assert state.progress["completed_units"] == 1
    assert not hasattr(state, "export_result")


def test_langgraph_workflow_populates_slide_unit_state() -> None:
    state = run_content_generation(
        ContentGenerationRequest(
            content_type="slide_deck",
            topic="人工智能基础导论",
            user_prompt="生成一份课件",
        )
    )

    assert state.status == "completed"
    assert state.outline is not None
    assert state.outline.units[0].unit_type == "slide"
    assert state.unit_results[state.outline.units[0].id].status == "completed"
    assert state.content_spec is not None
    assert isinstance(state.content_spec, SlideDeckSpec)
    assert state.content_spec.slides[0].outline_unit_id == state.outline.units[0].id
    assert state.content_spec.slides[0].required_elements
    assert state.elements
    assert state.render_model is not None
    assert state.render_model.render_type == "slide_deck"
