import pytest
from pydantic import ValidationError

from app.content_types.base import fixed_element_flags
from app.content_types.registry import get_content_type_profile
from app.core.config import get_settings
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.normalize_request_node import normalize_request


@pytest.mark.parametrize(
    ("content_type", "expect_images"),
    [
        ("lecture", True),
        ("slide_deck", True),
        ("social_post", True),
        ("podcast_script", False),
        ("interactive_html", False),
    ],
)
def test_fixed_element_flags_follow_content_type(content_type: str, expect_images: bool) -> None:
    flags = fixed_element_flags(get_content_type_profile(content_type).element_policy)

    assert flags == {
        "include_images": expect_images,
        "include_charts": False,
        "include_mindmap": False,
    }


def test_normalize_request_ignores_legacy_multimodal_options() -> None:
    state = ContentGenerationState(
        request_id="task_legacy_options",
        content_type="lecture",
        topic="固定多模态",
        user_prompt="生成测试内容",
        raw_request={
            "generation_options": {
                "include_images": False,
                "include_charts": True,
                "include_mindmap": True,
            }
        },
    )

    normalized = normalize_request(state)["normalized_request"]

    assert normalized["include_images"] is True
    assert normalized["include_charts"] is False
    assert normalized["include_mindmap"] is False


def test_lecture_fixed_policy_keeps_one_image_per_section(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.workflows.content_generation_graph import run_content_generation

    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()
    try:
        state = run_content_generation(
            ContentGenerationRequest(
                content_type="lecture",
                topic="固定多模态",
                user_prompt="生成测试内容",
                generation_options=GenerationOptions(section_count=1),
            )
        )
    finally:
        get_settings.cache_clear()

    assert state.content_spec is not None
    section = state.content_spec.sections[0]
    image_specs = [item for item in section.required_elements if item.type == "image"]
    assert len(image_specs) == 1
    assert {element.type for element in state.elements} == {"image"}


def test_multimodal_switch_fields_are_removed_from_request_schema() -> None:
    for field in ("include_images", "include_charts", "include_mindmap"):
        with pytest.raises(ValidationError):
            GenerationOptions(**{field: True})
