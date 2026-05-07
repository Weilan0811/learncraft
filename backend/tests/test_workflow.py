from app.schemas.request import ContentGenerationRequest
from app.workflows.content_generation_graph import run_content_generation


def test_workflow_stub_populates_generation_state() -> None:
    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="人工智能基础导论",
            user_prompt="生成一份讲义",
        )
    )

    assert state.status == "completed"
    assert state.outline is not None
    assert state.content_spec is not None
    assert state.elements
    assert state.render_model is not None
    assert not hasattr(state, "export_result")
