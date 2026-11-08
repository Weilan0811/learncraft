from app.content_types.registry import get_content_type_profile
from app.schemas.base import ContentType
from app.schemas.request import ContentGenerationRequest


def test_content_type_profiles_register_current_generation_types() -> None:
    lecture = get_content_type_profile("lecture")
    slide_deck = get_content_type_profile("slide_deck")
    social_post = get_content_type_profile("social_post")

    assert lecture.content_type == "lecture"
    assert lecture.unit_type == "section"
    assert lecture.requires_outline is True
    assert lecture.generation_mode == "unit_loop"
    assert lecture.planner_prompt_name == "lecture_outline.md"
    assert slide_deck.content_type == "slide_deck"
    assert slide_deck.unit_type == "slide"
    assert slide_deck.requires_outline is True
    assert slide_deck.generation_mode == "unit_loop"
    assert slide_deck.planner_prompt_name == "slide_outline.md"
    assert social_post.content_type == "social_post"
    assert social_post.unit_type == "article"
    assert social_post.requires_outline is False
    assert social_post.generation_mode == "direct"
    assert social_post.exporter_types == ("html", "image_assets")
    podcast = get_content_type_profile("podcast_script")
    assert podcast.content_type == "podcast_script"
    assert podcast.unit_type == "podcast"
    assert podcast.requires_outline is False
    assert podcast.generation_mode == "direct"
    assert podcast.exporter_types == ("markdown", "audio")
    interactive_html = get_content_type_profile("interactive_html")
    assert "zip" not in interactive_html.exporter_types
    assert "pptx" not in slide_deck.exporter_types


def test_request_schema_accepts_social_post_as_registered_generation_type() -> None:
    request = ContentGenerationRequest(
        content_type="social_post",
        topic="AI basics",
        user_prompt="Generate a social post",
    )

    assert request.content_type == "social_post"
    assert get_content_type_profile(request.content_type).content_type == "social_post"


def test_request_schema_accepts_podcast_as_registered_generation_type() -> None:
    request = ContentGenerationRequest(
        content_type="podcast_script",
        topic="AI basics",
        user_prompt="Generate a podcast script",
    )

    assert request.content_type == "podcast_script"
    assert get_content_type_profile(request.content_type).content_type == "podcast_script"


def test_content_type_literal_exports_future_types_for_schema_boundaries() -> None:
    content_type: ContentType = "podcast_script"

    assert content_type == "podcast_script"
