import pytest

from app.core.config import get_settings
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.schemas.outline import Outline, OutlineUnit
from app.schemas.specs import InteractiveHtmlSectionSpec, InteractiveHtmlTeachingBlock, LectureSpec, SlideDeckSpec
from app.schemas.state import ContentGenerationState
from app.workflows.content_generation_graph import run_content_generation


def test_langgraph_workflow_populates_lecture_unit_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()
    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="人工智能基础导论",
            user_prompt="生成一份讲义",
            generation_options=GenerationOptions(section_count=1),
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
    assert {element.type for element in state.elements} == {"image"}
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


def test_langgraph_workflow_does_not_generate_mindmap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()

    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="AI basics",
            user_prompt="Generate a lecture",
            generation_options=GenerationOptions(max_section_count=1),
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
            generation_options=GenerationOptions(max_section_count=1),
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


def test_real_provider_unit_spec_error_is_not_silently_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "real")
    monkeypatch.delenv("CONTENT_GENERATOR_ALLOW_FALLBACK", raising=False)
    get_settings.cache_clear()

    from app.generators.unit_specs import lecture

    def fail_generation(*args: object, **kwargs: object) -> object:
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(lecture, "generate_lecture_unit_spec_with_llm", fail_generation)
    state = ContentGenerationState(
        request_id="task_no_fallback",
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
        normalized_request={"allow_fallback": False},
    )
    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type="section",
        title="Foundations",
        goal="Understand the basics.",
        core_message="AI systems turn inputs into useful outputs.",
    )

    with pytest.raises(RuntimeError, match="provider exploded"):
        lecture.build_lecture_unit_spec(state, unit, [])

    get_settings.cache_clear()


def test_real_provider_unit_spec_can_use_explicit_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "real")
    get_settings.cache_clear()

    from app.generators.unit_specs import lecture

    def fail_generation(*args: object, **kwargs: object) -> object:
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(lecture, "generate_lecture_unit_spec_with_llm", fail_generation)
    state = ContentGenerationState(
        request_id="task_allow_fallback",
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
        normalized_request={"allow_fallback": True},
    )
    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type="section",
        title="Foundations",
        goal="Understand the basics.",
        core_message="AI systems turn inputs into useful outputs.",
    )

    spec = lecture.build_lecture_unit_spec(state, unit, [])

    assert spec.outline_unit_id == "unit_001"
    get_settings.cache_clear()


def test_interactive_html_llm_unit_spec_uses_current_unit_section_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "real")
    get_settings.cache_clear()

    from app.generators.unit_specs.interactive_html import build_interactive_html_unit_spec
    from app.workflows.nodes.validator_node import validate_unit_spec

    unit = OutlineUnit(
        id="unit_001",
        order=1,
        unit_type="interactive_section",
        title="智能体基础",
        goal="理解智能体的基本组成。",
        core_message="智能体通过感知、推理和行动完成任务。",
    )
    state = ContentGenerationState(
        request_id="task_interactive_id",
        content_type="interactive_html",
        topic="智能体基础",
        user_prompt="生成互动课件",
        normalized_request={"allow_fallback": False},
        outline=Outline(
            id="outline_task_interactive_id",
            content_type="interactive_html",
            title="智能体基础",
            units=[unit],
        ),
        current_unit_id=unit.id,
        pending_unit_ids=[unit.id],
    )

    class PromptFollowingLLM:
        def generate_structured(self, prompt: str, schema):
            marker = "- unit_spec_id: "
            section_id = prompt.split(marker, 1)[1].splitlines()[0].strip()
            assert schema is InteractiveHtmlSectionSpec
            return InteractiveHtmlSectionSpec(
                section_id=section_id,
                title=unit.title,
                learning_goal=unit.goal,
                narrative_goal="帮助学习者理解智能体的基本组成。",
                teaching_flow=[
                    InteractiveHtmlTeachingBlock(
                        block_id=f"{section_id}_intro",
                        block_type="intro",
                        title="建立学习背景",
                        teaching_role="set_context",
                        content_goal="说明为什么要理解智能体。",
                        must_cover=["智能体"],
                    ),
                    InteractiveHtmlTeachingBlock(
                        block_id=f"{section_id}_concept",
                        block_type="concept_explanation",
                        title="解释核心组成",
                        teaching_role="explain_core",
                        content_goal="解释感知、推理和行动的关系。",
                        must_cover=["感知", "推理", "行动"],
                    ),
                    InteractiveHtmlTeachingBlock(
                        block_id=f"{section_id}_summary",
                        block_type="summary",
                        title="收束关键理解",
                        teaching_role="wrap_up",
                        content_goal="总结智能体完成任务的闭环。",
                        must_cover=["任务闭环"],
                    ),
                ],
            )

    monkeypatch.setattr("app.generators.unit_specs.interactive_html.get_llm_service", lambda: PromptFollowingLLM())

    unit_spec = build_interactive_html_unit_spec(state, unit, [])
    result = validate_unit_spec(state.model_copy(update={"current_unit_spec": unit_spec}))

    assert unit_spec.section_id == unit.id
    assert result["spec_validation_report"]["passed"] is True
    get_settings.cache_clear()
