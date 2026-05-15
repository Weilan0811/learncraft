from app.schemas.elements import ChartElement, ImageElement, MindmapElement, TextElement
from app.core.task import TaskStatus
from app.schemas.outline import Outline, OutlineSection, OutlineUnit
from app.schemas.render import SlidePageModel
from app.schemas.request import ContentGenerationRequest
from app.schemas.state import ContentGenerationState
from app.schemas.specs import LectureSection, LectureSpec, RequiredElementSpec, SlideSpecElement, SlideSpecPage, TextBlock
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
        id="slide_unit_stub",
        outline_unit_id="unit_stub",
        order=1,
        title="什么是人工智能",
        core_message="人工智能研究机器智能行为。",
        layout="image_text",
        design_intent="Pair the core explanation with a supporting teaching visual.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        elements=[
            SlideSpecElement(id="slide_stub_title", type="text", content="什么是人工智能", metadata={"role": "title"}),
            SlideSpecElement(
                id="slide_stub_explanation",
                type="text",
                content="人工智能研究机器智能行为。",
                metadata={"role": "explanation"},
            ),
            SlideSpecElement(
                id="slide_stub_bullet_list",
                type="text",
                content="• 定义\n• 关键关系",
                metadata={"role": "bullet_list"},
            ),
            SlideSpecElement(
                id="slide_stub_takeaway",
                type="text",
                content="理解人工智能的基本定义",
                metadata={"role": "takeaway"},
            ),
            SlideSpecElement(
                id="slide_stub_visual_ref",
                type="element_ref",
                element_id="img_stub",
                metadata={"role": "visual"},
            ),
        ],
        required_elements=[required_image.model_copy(update={"source_unit_id": "slide_unit_stub"})],
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
        id="slide_unit_stub",
        outline_unit_id="unit_stub",
        order=1,
        title="什么是人工智能",
        core_message="人工智能研究机器智能行为。",
        layout="image_text",
        design_intent="Pair the core explanation with a supporting teaching visual.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        speaker_notes="Explain the definition and connect it to the unit goal.",
        elements=[
            SlideSpecElement(
                id="slide_stub_title",
                type="text",
                content="什么是人工智能",
                metadata={"role": "title"},
            ),
            SlideSpecElement(
                id="slide_stub_explanation",
                type="text",
                content="人工智能研究机器智能行为。",
                metadata={"role": "explanation"},
            ),
            SlideSpecElement(
                id="slide_stub_bullet_list",
                type="text",
                content="• 定义\n• 关键关系",
                metadata={"role": "bullet_list"},
            ),
            SlideSpecElement(
                id="slide_stub_takeaway",
                type="text",
                content="理解人工智能的基本定义",
                metadata={"role": "takeaway"},
            ),
            SlideSpecElement(
                id="slide_stub_visual_ref",
                type="element_ref",
                element_id="img_stub",
                metadata={"role": "visual"},
            ),
        ],
        required_elements=[
            RequiredElementSpec(
                element_id="img_stub",
                type="image",
                title="示意图",
                purpose="展示核心概念",
                instruction="生成示意图",
                source_unit_id="slide_unit_stub",
                source_outline_unit_id="unit_stub",
            ),
        ],
    )

    assert slide.layout == "image_text"
    assert slide.elements[1].metadata["role"] == "explanation"

    try:
        SlideSpecPage(
            id="slide_unit_stub",
            outline_unit_id="unit_stub",
            order=1,
            title="未知布局",
            core_message="这应该被拒绝。",
            design_intent="Reject unsupported layouts.",
            layout_hints={"supported_renderer": "scenekit.slide/v1"},
            layout="freeform-poster",
            elements=[
                SlideSpecElement(id="slide_stub_title", type="text", content="未知布局", metadata={"role": "title"}),
            ],
        )
    except ValidationError as exc:
        assert "layout" in str(exc)
    else:
        raise AssertionError("SlideSpecPage should reject unsupported slide layouts")


def test_slide_spec_page_rejects_outputs_that_fail_workflow_contract() -> None:
    try:
        SlideSpecPage(
            id="slide_1",
            outline_unit_id=None,
            order=None,
            title="Example Slide",
            core_message="This is the core message.",
            layout="image_text",
            layout_hints={},
            elements=[
                SlideSpecElement(
                    id="elem_1",
                    type="text",
                    content="Some content",
                    metadata={},
                ),
            ],
            required_elements=[
                RequiredElementSpec(
                    element_id="req_elem_1",
                    type="image",
                    title="Required Image",
                    purpose="To illustrate the point",
                    instruction="Insert relevant image here",
                    source_unit_id="unit_1",
                    source_outline_unit_id="outline_1",
                )
            ],
        )
    except ValidationError as exc:
        message = str(exc)
        assert "outline_unit_id" in message
        assert "order" in message
    else:
        raise AssertionError("SlideSpecPage should reject workflow-invalid LLM output")

    try:
        SlideSpecPage(
            id="slide_slide_3",
            outline_unit_id="slide_3",
            order=3,
            title="Example Slide",
            core_message="This is the core message.",
            layout="image_text",
            design_intent="Explain the core message.",
            speaker_notes="Use this slide to introduce the topic.",
            layout_hints={"supported_renderer": "scenekit.slide/v1"},
            elements=[
                SlideSpecElement(id="elem_1", type="text", content="Some content", metadata={}),
            ],
        )
    except ValidationError as exc:
        assert "role" in str(exc) or "layout" in str(exc)
    else:
        raise AssertionError("SlideSpecPage should reject missing required roles")

    try:
        SlideSpecPage(
            id="slide_1",
            outline_unit_id="slide_3",
            order=1,
            title="Example Slide",
            core_message="This is the core message.",
            layout="image_text",
            design_intent="Explain the core message.",
            speaker_notes="Use this slide to introduce the topic.",
            layout_hints={"supported_renderer": "scenekit.slide/v1"},
            elements=[
                SlideSpecElement(id="elem_title", type="text", content="Example Slide", metadata={"role": "title"}),
                SlideSpecElement(id="elem_explanation", type="text", content="Some content", metadata={"role": "explanation"}),
                SlideSpecElement(id="elem_bullet_list", type="text", content="• Point 1\n• Point 2", metadata={"role": "bullet_list"}),
                SlideSpecElement(id="elem_takeaway", type="text", content="Key takeaway", metadata={"role": "takeaway"}),
                SlideSpecElement(id="elem_visual", type="element_ref", element_id="img_1", metadata={"role": "visual"}),
            ],
            required_elements=[
                RequiredElementSpec(
                    element_id="img_1",
                    type="image",
                    title="Image",
                    purpose="Visual",
                    instruction="Generate image",
                    source_unit_id="slide_1",
                    source_outline_unit_id="slide_3",
                ),
            ],
        )
    except ValidationError as exc:
        message = str(exc)
        assert "slide id" in message
    else:
        raise AssertionError("SlideSpecPage should reject mismatched slide id and outline unit")

    try:
        SlideSpecElement(
            id="elem_2",
            type="image",
            element_id="req_elem_1",
            metadata={"role": "visual"},
        )
    except ValidationError as exc:
        assert "type" in str(exc)
    else:
        raise AssertionError("SlideSpecElement should reject non-contract element types")
