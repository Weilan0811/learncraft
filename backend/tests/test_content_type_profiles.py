import pytest

from app.content_types.registry import get_content_type_profile
from app.schemas.base import ContentType
from app.schemas.request import ContentGenerationRequest


def test_content_type_profiles_register_current_generation_types() -> None:
    lecture = get_content_type_profile("lecture")
    slide_deck = get_content_type_profile("slide_deck")

    assert lecture.content_type == "lecture"
    assert lecture.unit_type == "section"
    assert lecture.requires_outline is True
    assert lecture.planner_prompt_name == "lecture_outline.md"
    assert slide_deck.content_type == "slide_deck"
    assert slide_deck.unit_type == "slide"
    assert slide_deck.requires_outline is True
    assert slide_deck.planner_prompt_name == "slide_outline.md"


def test_request_schema_accepts_open_content_type_but_registry_rejects_unsupported_generation_type() -> None:
    request = ContentGenerationRequest(
        content_type="social_post",
        topic="AI basics",
        user_prompt="Generate a social post",
    )

    assert request.content_type == "social_post"

    with pytest.raises(ValueError, match="Unsupported content type"):
        get_content_type_profile(request.content_type)


def test_content_type_literal_exports_future_types_for_schema_boundaries() -> None:
    content_type: ContentType = "podcast_script"

    assert content_type == "podcast_script"
