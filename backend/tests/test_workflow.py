import pytest

from app.core.config import get_settings
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.schemas.specs import LectureSpec, SlideDeckSpec
from app.workflows.content_generation_graph import run_content_generation


def test_langgraph_workflow_populates_lecture_unit_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()
    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="人工智能基础导论",
            user_prompt="生成一份讲义",
            generation_options=GenerationOptions(include_images=True, include_mindmap=True, section_count=1),
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
    assert len([block for block in state.content_spec.sections[0].blocks if block.type == "text"]) >= 2
    assert state.elements
    assert {element.type for element in state.elements} == {"image", "mindmap"}
    assert state.render_model is not None
    assert state.current_node == "finalize_task"
    assert state.progress["completed_units"] == 1
    assert not hasattr(state, "export_result")
    get_settings.cache_clear()


def test_langgraph_workflow_populates_slide_unit_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()
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
    first_page = state.render_model.pages[0].page
    assert first_page.width == 960
    assert first_page.height == 540
    assert first_page.theme.fontName
    assert first_page.elements
    assert all(element.left >= 0 and element.top >= 0 for element in first_page.elements)
    image_elements = [element for element in first_page.elements if element.type == "image"]
    assert image_elements
    assert image_elements[0].src.startswith("/api/assets/")
    assert not hasattr(image_elements[0], "url")
    assert first_page.speakerNotes
    get_settings.cache_clear()


def test_langgraph_workflow_does_not_force_mindmap_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()

    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="AI basics",
            user_prompt="Generate a lecture",
            generation_options=GenerationOptions(include_images=True, include_mindmap=False, max_section_count=1),
        )
    )

    assert state.status == "completed"
    assert {element.type for element in state.elements} == {"image"}
    assert state.content_spec is not None
    assert isinstance(state.content_spec, LectureSpec)
    assert all(item.type != "mindmap" for item in state.content_spec.sections[0].required_elements)
    get_settings.cache_clear()


def test_workflow_image_specs_request_local_illustration_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()

    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="AI timeline",
            user_prompt="Generate a lecture with an illustration",
            generation_options=GenerationOptions(include_images=True, include_mindmap=False, max_section_count=1),
        )
    )

    assert state.content_spec is not None
    assert isinstance(state.content_spec, LectureSpec)
    image_specs = [
        item
        for section in state.content_spec.sections
        for item in section.required_elements
        if item.type == "image"
    ]
    assert image_specs
    assert all("local illustration asset" in item.instruction for item in image_specs)
    assert all("Do not create a full presentation slide" in item.instruction for item in image_specs)
    get_settings.cache_clear()
