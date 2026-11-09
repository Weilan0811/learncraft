import pytest
from pydantic import ValidationError

from app.schemas.request import ContentGenerationRequest, GenerationOptions


def test_step1_generation_options_accepts_supported_fields():
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="人工智能基础导论",
        user_prompt="生成讲义",
        generation_options=GenerationOptions(
            language="zh-CN",
            audience="大学生",
            difficulty="introductory",
            style="educational",
            duration_minutes=30,
            section_count=5,
            slide_count=None,
            output_depth="detailed",
            image_style="真实感",
            citation_policy="strict",
            slide_theme=None,
            speaker_notes=True,
            pdf_options={"page_size": "A4"},
        ),
    )
    assert request.generation_options.audience == "大学生"
    assert request.generation_options.duration_minutes == 30
    assert not hasattr(request.generation_options, "include_mindmap")


def test_step1_old_request_without_options():
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="Python入门",
        user_prompt="生成课件",
    )
    assert request.generation_options.slide_count is None
    assert request.generation_options.max_slide_count == 12


def test_step1_normalize_request_includes_supported_fields():
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="测试主题",
        user_prompt="测试",
        generation_options=GenerationOptions(
            audience="中学生",
            duration_minutes=25,
        ),
    )
    assert request.generation_options.audience == "中学生"
    assert request.generation_options.duration_minutes == 25


def test_step1_multimodal_switch_fields_are_rejected():
    with pytest.raises(ValidationError):
        GenerationOptions(include_images=True)

    with pytest.raises(ValidationError):
        ContentGenerationRequest(
            content_type="lecture",
            topic="测试主题",
            user_prompt="测试",
            generation_options={"include_mindmap": True},
        )
