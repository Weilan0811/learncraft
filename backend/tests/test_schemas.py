from app.schemas.elements import ChartElement, ImageElement, MindmapElement, TextElement
from app.schemas.outline import Outline, OutlineSection, OutlineUnit
from app.core.task import TaskStatus
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState
from app.schemas.specs import LectureSection, LectureSpec, RequiredElementSpec, SlideSpecPage, TextBlock
from app.workflows.nodes.normalize_request_node import normalize_request
from pydantic import ValidationError


def test_content_generation_request_accepts_mvp_content_types() -> None:
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="人工智能基础导论",
        user_prompt="生成课程幻灯片",
    )

    assert request.content_type == "slide_deck"
    assert request.generation_options.language == "zh-CN"
    assert request.generation_options.slide_count is None
    assert request.generation_options.max_slide_count == 12


def test_generation_options_use_max_counts_without_forcing_exact_counts() -> None:
    slide_request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="AI basics",
        user_prompt="Generate a slide deck",
    )
    lecture_request = ContentGenerationRequest(
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a lecture",
    )

    assert slide_request.generation_options.slide_count is None
    assert slide_request.generation_options.max_slide_count == 12
    assert lecture_request.generation_options.section_count is None
    assert lecture_request.generation_options.max_section_count == 8


def test_normalize_request_maps_legacy_counts_to_maximums() -> None:
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="AI basics",
        user_prompt="Generate a slide deck",
        generation_options={"slide_count": 5, "include_mindmap": False},
    )
    state = ContentGenerationState(
        request_id="test_legacy_counts",
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        raw_request=request.model_dump(mode="json"),
        status=TaskStatus.running,
    )

    normalized = normalize_request(state)["normalized_request"]

    assert normalized["slide_count"] == 5
    assert normalized["max_slide_count"] == 5


def test_outline_units_reject_recommended_elements() -> None:
    try:
        OutlineUnit(
            id="unit_stub",
            order=1,
            unit_type="section",
            title="What is AI",
            goal="Explain the core idea",
            core_message="AI systems model intelligent behavior.",
            recommended_elements=[{"type": "image", "purpose": "show concept"}],
            retrieval_queries=["AI definition"],
        )
    except ValidationError as exc:
        assert "recommended_elements" in str(exc)
    else:
        raise AssertionError("recommended_elements should not be part of OutlineUnit")


def test_content_generation_request_rejects_output_formats() -> None:
    try:
        ContentGenerationRequest(
            content_type="slide_deck",
            topic="AI basics",
            user_prompt="Generate a slide deck",
            output_formats=["slide_json"],
        )
    except ValidationError as exc:
        assert "output_formats" in str(exc)
    else:
        raise AssertionError("output_formats should be rejected by ContentGenerationRequest")


def test_core_content_schemas_keep_required_extension_fields() -> None:
    required_image = RequiredElementSpec(
        element_id="img_stub",
        type="image",
        title="概念示意图",
        purpose="展示核心概念",
        instruction="生成一张清晰的教学示意图。",
        source_unit_id="sec_stub",
        source_outline_unit_id="unit_stub",
        source_chunk_ids=["chunk_stub"],
    )
    outline = Outline(
        id="outline_stub",
        content_type="lecture",
        title="人工智能基础导论",
        audience="本科一年级学生",
        learning_objectives=["理解人工智能的基本概念"],
        units=[
            OutlineUnit(
                id="unit_stub",
                order=1,
                unit_type="section",
                title="什么是人工智能",
                goal="理解基本定义",
                core_message="人工智能研究机器智能行为。",
                key_points=["定义"],
                retrieval_queries=["人工智能 定义"],
                source_chunk_ids=["chunk_stub"],
            )
        ],
        sections=[
            OutlineSection(
                id="sec_stub",
                title="什么是人工智能",
                goal="理解基本定义",
                key_points=["定义"],
                citations=["chunk_stub"],
            )
        ],
    )
    spec = LectureSpec(
        id="lecture_stub",
        title=outline.title,
        metadata={"language": "zh-CN"},
        objectives=outline.learning_objectives,
        sections=[
            LectureSection(
                id="sec_stub",
                title="什么是人工智能",
                summary="介绍基础概念。",
                blocks=[
                    TextBlock(
                        id="block_stub",
                        title="概念解释",
                        content="人工智能是研究机器智能行为的领域。",
                        citations=["chunk_stub"],
                    )
                ],
                outline_unit_id="unit_stub",
                required_elements=[required_image],
                source_chunk_ids=["chunk_stub"],
            )
        ],
    )
    slide = SlideSpecPage(
        id="slide_stub",
        outline_unit_id="unit_stub",
        title="什么是人工智能",
        core_message="人工智能研究机器智能行为。",
        elements=[],
        required_elements=[required_image.model_copy(update={"source_unit_id": "slide_stub"})],
        speaker_notes="用于建立基本概念。",
    )

    assert spec.type == "lecture"
    assert spec.version == "content.spec/v1"
    assert spec.sections[0].blocks[0].type == "text"
    assert spec.sections[0].required_elements[0].element_id == "img_stub"
    assert slide.required_elements[0].source_outline_unit_id == "unit_stub"


def test_element_schemas_have_shared_required_fields() -> None:
    elements = [
        TextElement(id="txt_stub", title="正文", content="占位文本"),
        ImageElement(
            id="img_stub",
            title="示意图",
            prompt="clean educational illustration",
            asset_url="/api/assets/img_stub",
            alt_text="示意图",
            source_unit_id="slide_stub",
            source_outline_unit_id="unit_stub",
            source_chunk_ids=["chunk_stub"],
            generation_info={"provider": "stub"},
        ),
        ChartElement(
            id="chart_stub",
            title="学习方式对比",
            chart_type="bar",
            x_axis={"name": "方式", "data": ["阅读"]},
            y_axis={"name": "效果"},
            series=[{"name": "效果", "data": [90]}],
        ),
        MindmapElement(
            id="mindmap_stub",
            title="知识结构",
            markdown="# 人工智能",
            source_unit_id="sec_stub",
            source_outline_unit_id="unit_stub",
            source_chunk_ids=["chunk_stub"],
            render_hints={"renderer": "markmap"},
        ),
    ]

    assert [element.type for element in elements] == ["text", "image", "chart", "mindmap"]
    assert elements[1].source_outline_unit_id == "unit_stub"
    assert elements[3].render_hints["renderer"] == "markmap"
