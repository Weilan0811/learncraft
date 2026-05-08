from app.schemas.elements import ChartElement, ImageElement, MindmapElement, TextElement
from app.schemas.outline import Outline, OutlineSection, OutlineUnit, RecommendedElement
from app.schemas.render import SlidePageModel
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import LectureSection, LectureSpec, RequiredElementSpec, SlideSpecElement, SlideSpecPage, TextBlock
from pydantic import ValidationError


def test_content_generation_request_accepts_mvp_content_types() -> None:
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="人工智能基础导论",
        user_prompt="生成课程幻灯片",
    )

    assert request.content_type == "slide_deck"
    assert request.generation_options.language == "zh-CN"


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
                recommended_elements=[
                    RecommendedElement(type="image", purpose="展示核心概念", priority="high"),
                ],
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
                recommended_elements=["text", "image"],
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
    assert outline.units[0].recommended_elements[0].type == "image"
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


def test_slide_page_model_validates_scenekit_slide_v1_contract() -> None:
    page = SlidePageModel(
        page={
            "id": "slide_stub",
            "title": "什么是人工智能",
            "width": 960,
            "height": 540,
            "background": {"type": "solid", "color": "#FFFFFF"},
            "theme": {
                "fontName": "Arial",
                "fontColor": "#111827",
                "backgroundColor": "#FFFFFF",
                "themeColors": ["#2563eb", "#0f766e"],
            },
            "elements": [
                {
                    "id": "title",
                    "type": "text",
                    "left": 48,
                    "top": 40,
                    "width": 720,
                    "height": 72,
                    "rotate": 0,
                    "content": "<p>什么是人工智能</p>",
                }
            ],
            "speakerNotes": "用于建立基本概念。",
        }
    )

    assert page.page.width == 960
    assert page.page.elements[0].type == "text"
    assert page.page.speakerNotes == "用于建立基本概念。"


def test_slide_page_model_rejects_elements_without_position() -> None:
    try:
        SlidePageModel(
            page={
                "id": "slide_stub",
                "title": "什么是人工智能",
                "width": 960,
                "height": 540,
                "theme": {
                    "fontName": "Arial",
                    "fontColor": "#111827",
                    "backgroundColor": "#FFFFFF",
                    "themeColors": ["#2563eb"],
                },
                "elements": [{"id": "title", "type": "text", "content": "<p>缺少坐标</p>"}],
            }
        )
    except ValidationError as exc:
        assert "left" in str(exc)
        assert "height" in str(exc)
    else:
        raise AssertionError("SlidePageModel should reject scenekit elements without geometry")


def test_slide_spec_page_rejects_unknown_layouts_and_keeps_element_roles() -> None:
    slide = SlideSpecPage(
        id="slide_stub",
        title="什么是人工智能",
        core_message="人工智能研究机器智能行为。",
        layout="title-content-visual",
        elements=[
            SlideSpecElement(
                id="slide_stub_body",
                type="text",
                content="人工智能研究机器智能行为。",
                metadata={"role": "body", "emphasis": "primary"},
            )
        ],
    )

    assert slide.layout == "title-content-visual"
    assert slide.elements[0].metadata["role"] == "body"

    try:
        SlideSpecPage(
            id="slide_bad",
            title="未知布局",
            core_message="这应该被拒绝。",
            layout="freeform-poster",
        )
    except ValidationError as exc:
        assert "layout" in str(exc)
    else:
        raise AssertionError("SlideSpecPage should reject unsupported slide layouts")
