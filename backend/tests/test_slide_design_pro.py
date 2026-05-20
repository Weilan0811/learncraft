from pathlib import Path

from app.generators.unit_spec_generators import normalize_slide_spec
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.elements import ImageElement
from app.schemas.outline import OutlineUnit
from app.schemas.request import ContentGenerationRequest
from app.schemas.specs import RequiredElementSpec, SlideDeckSpec, SlideSpecElement, SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.services.image_generation_service import APIMartImageGenerationService
from app.workflows.nodes.normalize_request_node import normalize_request
from app.workflows.nodes.validator_node import validate_unit_spec
from app.core.task import TaskStatus
from pydantic import ValidationError


def _unit() -> OutlineUnit:
    return OutlineUnit(
        id="unit_1",
        order=1,
        unit_type="slide",
        title="智能体协作",
        goal="理解智能体协作的基本机制",
        core_message="智能体通过分工、共享状态和结果合成完成复杂任务。",
        key_points=["分工降低单点复杂度", "共享状态保持上下文", "结果合成形成最终答案"],
        visual_strategy="image_text",
        retrieval_queries=["智能体 协作"],
        source_chunk_ids=["chunk_1"],
    )


def _state() -> ContentGenerationState:
    request = ContentGenerationRequest(
        content_type="slide_deck",
        topic="智能体协作",
        user_prompt="生成教学幻灯片",
    )
    state = ContentGenerationState(
        request_id="req_1",
        content_type=request.content_type,
        topic=request.topic,
        user_prompt=request.user_prompt,
        raw_request=request.model_dump(mode="json"),
        status=TaskStatus.running,
    )
    state.normalized_request = normalize_request(state)["normalized_request"]  # type: ignore[assignment]
    state.current_unit_index = 0
    state.current_unit_id = "unit_1"
    state.pending_unit_ids = ["unit_1"]
    state.outline = None
    return state


def _image_required(element_id: str = "image_req_1") -> RequiredElementSpec:
    return RequiredElementSpec(
        element_id=element_id,
        type="image",
        title="协作示意图",
        purpose="辅助说明智能体协作",
        instruction="生成一个低信息密度教学插画。",
        aspect_ratio="4:3",
        source_unit_id="slide_unit_1",
        source_outline_unit_id="unit_1",
        source_chunk_ids=["chunk_1"],
    )


def test_slide_spec_page_accepts_new_two_card_image_text_contract() -> None:
    slide = SlideSpecPage(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体通过分工完成复杂任务。",
        layout="image_text",
        design_intent="Use two cards and one visual.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        speaker_notes="讲解智能体协作机制。",
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(
                id="lead",
                type="text",
                content="智能体协作把复杂任务拆成多个清晰职责。",
                metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
            ),
            SlideSpecElement(
                id="support",
                type="text",
                content="• 分工明确\n• 状态共享\n• 结果合成",
                metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
            ),
            SlideSpecElement(id="summary", type="text", content="协作让复杂任务变得可控", metadata={"role": "summary_text"}),
            SlideSpecElement(id="visual", type="element_ref", element_id="image_req_1", metadata={"role": "visual"}),
        ],
        required_elements=[_image_required()],
        source_chunk_ids=["chunk_1"],
    )

    roles = [element.metadata["role"] for element in slide.elements]

    assert roles == ["title", "lead_card", "support_card", "summary_text", "visual"]


def test_slide_spec_page_rejects_image_text_cards_without_display_labels() -> None:
    try:
        SlideSpecPage(
            id="slide_unit_1",
            outline_unit_id="unit_1",
            order=1,
            title="智能体协作",
            core_message="智能体通过分工完成复杂任务。",
            layout="image_text",
            design_intent="Use two cards and one visual.",
            layout_hints={"supported_renderer": "scenekit.slide/v1"},
            speaker_notes="讲解智能体协作机制。",
            elements=[
                SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
                SlideSpecElement(id="lead", type="text", content="核心解释。", metadata={"role": "lead_card"}),
                SlideSpecElement(
                    id="support",
                    type="text",
                    content="• 要点一\n• 要点二",
                    metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
                ),
                SlideSpecElement(id="summary", type="text", content="协作让复杂任务变得可控", metadata={"role": "summary_text"}),
                SlideSpecElement(id="visual", type="element_ref", element_id="image_req_1", metadata={"role": "visual"}),
            ],
            required_elements=[_image_required()],
        )
    except ValidationError as exc:
        assert "display_label" in str(exc)
    else:
        raise AssertionError("image_text card elements should require display_label")


def test_normalize_slide_spec_maps_legacy_image_text_roles_to_two_cards() -> None:
    raw = SlideSpecPage.model_construct(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体通过分工、共享状态和结果合成完成复杂任务。",
        layout="image_text",
        design_intent="",
        theme_variant=None,
        layout_hints={},
        speaker_notes="",
        source_chunk_ids=["chunk_1"],
        required_elements=[],
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(id="explanation", type="text", content="智能体协作把复杂任务拆成多个清晰职责。", metadata={"role": "explanation"}),
            SlideSpecElement(id="bullets", type="text", content="• 分工明确\n• 状态共享\n• 结果合成", metadata={"role": "bullet_list"}),
            SlideSpecElement(id="takeaway", type="text", content="协作让复杂任务变得可控", metadata={"role": "takeaway"}),
        ],
    )

    normalized = normalize_slide_spec(raw, _unit(), _state())
    roles = [element.metadata.get("role") for element in normalized.elements]

    assert "explanation" not in roles
    assert "bullet_list" not in roles
    assert "takeaway" not in roles
    assert roles.count("lead_card") == 1
    assert roles.count("support_card") == 1
    assert roles.count("summary_text") == 1
    assert normalized.elements[1].metadata["display_label"] == "核心解释"
    assert normalized.elements[2].metadata["display_label"] == "关键要点"
    assert normalized.required_elements[0].aspect_ratio == "4:3"
    assert "not a full slide" in normalized.required_elements[0].instruction
    assert "No title bar" in normalized.required_elements[0].instruction


def test_normalize_slide_spec_avoids_duplicate_lead_and_summary_text() -> None:
    raw = SlideSpecPage.model_construct(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体通过分工、共享状态和结果合成完成复杂任务。",
        layout="image_text",
        design_intent="",
        theme_variant=None,
        layout_hints={},
        speaker_notes="",
        source_chunk_ids=["chunk_1"],
        required_elements=[],
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(
                id="lead",
                type="text",
                content="智能体通过分工、共享状态和结果合成完成复杂任务。",
                metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
            ),
            SlideSpecElement(
                id="support",
                type="text",
                content="• 分工降低单点复杂度\n• 共享状态保持上下文\n• 结果合成形成最终答案",
                metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
            ),
        ],
    )

    normalized = normalize_slide_spec(raw, _unit(), _state())
    lead = next(element for element in normalized.elements if element.metadata.get("role") == "lead_card")
    summary = next(element for element in normalized.elements if element.metadata.get("role") == "summary_text")

    assert summary.content != lead.content
    assert summary.content == "重点关注分工降低单点复杂度"


def test_visual_summary_normalization_keeps_only_visual_and_plain_summary() -> None:
    raw = SlideSpecPage.model_construct(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体协作依赖分工、共享状态和结果合成。",
        layout="visual_summary",
        design_intent="",
        theme_variant=None,
        layout_hints={},
        speaker_notes="",
        source_chunk_ids=["chunk_1"],
        required_elements=[],
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(id="lead", type="text", content="应该被清理。", metadata={"role": "lead_card", "display_label": "核心解释"}),
            SlideSpecElement(id="takeaway", type="text", content="核心点：协作提升复杂任务质量", metadata={"role": "takeaway"}),
        ],
    )

    normalized = normalize_slide_spec(raw, _unit(), _state())
    roles = [element.metadata.get("role") for element in normalized.elements]

    assert roles == ["title", "summary_text", "visual"]
    assert normalized.elements[1].content == "协作提升复杂任务质量"
    assert normalized.required_elements[0].aspect_ratio == "21:9"
    assert "diagram asset" in normalized.required_elements[0].instruction
    assert "centered safe area" in normalized.required_elements[0].instruction
    assert "No outer title" in normalized.required_elements[0].instruction


def test_slide_renderer_outputs_two_cards_and_unprefixed_summary_bar() -> None:
    slide = SlideSpecPage(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体通过分工完成复杂任务。",
        layout="image_text",
        design_intent="Use two cards and one visual.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        speaker_notes="讲解智能体协作机制。",
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(
                id="lead",
                type="text",
                content="智能体协作把复杂任务拆成多个清晰职责。",
                metadata={"role": "lead_card", "display_label": "核心解释", "content_format": "paragraph"},
            ),
            SlideSpecElement(
                id="support",
                type="text",
                content="• 分工明确\n• 状态共享\n• 结果合成",
                metadata={"role": "support_card", "display_label": "关键要点", "content_format": "bullets"},
            ),
            SlideSpecElement(id="summary", type="text", content="协作让复杂任务变得可控", metadata={"role": "summary_text"}),
            SlideSpecElement(id="visual", type="element_ref", element_id="image_req_1", metadata={"role": "visual"}),
        ],
        required_elements=[_image_required()],
        source_chunk_ids=["chunk_1"],
    )
    deck = SlideDeckSpec(id="deck_1", title="智能体协作", slides=[slide])
    image = ImageElement(id="image_req_1", title="协作示意图", prompt="prompt", asset_url="/asset.png", alt_text="协作示意图")

    page = SlideRenderer().render(deck, [image]).pages[0].page
    text_content = "".join(getattr(element, "content", "") or "" for element in page.elements)
    ids = [element.id for element in page.elements]

    assert any("lead_card" in element_id for element_id in ids)
    assert any("support_card" in element_id for element_id in ids)
    assert "核心解释" not in text_content
    assert "关键要点" not in text_content
    assert "协作让复杂任务变得可控" in text_content
    assert "核心点：" not in text_content
    assert f"{slide.id}_summary_shape" not in ids

    title = next(element for element in page.elements if element.id == f"{slide.id}_title")
    lead_text = next(element for element in page.elements if element.id == f"{slide.id}_lead_card_text")
    support_text = next(element for element in page.elements if element.id == f"{slide.id}_support_card_text")
    summary_text = next(element for element in page.elements if element.id == f"{slide.id}_summary_text")
    lead_shape = next(element for element in page.elements if element.id == f"{slide.id}_lead_card_shape")
    support_shape = next(element for element in page.elements if element.id == f"{slide.id}_support_card_shape")
    visual_panel = next(element for element in page.elements if element.id == f"{slide.id}_visual_panel")

    assert title.width >= 760
    assert lead_text.top == 180
    assert support_text.top == 306
    assert support_shape.width >= lead_shape.width
    assert support_shape.width <= 440
    assert support_shape.height >= 128
    assert visual_panel.left - (support_shape.left + support_shape.width) >= 32
    assert support_text.content.count("<p>•") == 3
    assert summary_text.align == "center"
    assert summary_text.fill == "transparent"
    assert summary_text.left == 64
    assert summary_text.width == 832
    assert summary_text.top >= 452
    assert summary_text.height <= 28
    assert summary_text.fontSize <= 16


def test_slide_prompt_requires_distinct_image_text_summary() -> None:
    prompt = Path("backend/app/prompts/generator/slide_deck_spec.md").read_text(encoding="utf-8")

    assert "summary_text 不得复制或同义复述 lead_card" in prompt
    assert "不得直接复制 core_message" in prompt
    assert "summary_text 是否与 lead_card/core_message 形成互补而非重复" in prompt


def test_visual_summary_renderer_uses_taller_main_visual_area_and_transparent_summary() -> None:
    slide = SlideSpecPage(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作流程",
        core_message="智能体协作依赖分工、共享状态和结果合成。",
        layout="visual_summary",
        design_intent="Use a large centered diagram and plain summary.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        speaker_notes="讲解智能体协作机制。",
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作流程", metadata={"role": "title"}),
            SlideSpecElement(id="summary", type="text", content="协作流程需要清晰边界和结果合成", metadata={"role": "summary_text"}),
            SlideSpecElement(id="visual", type="element_ref", element_id="image_req_1", metadata={"role": "visual"}),
        ],
        required_elements=[_image_required()],
        source_chunk_ids=["chunk_1"],
    )
    deck = SlideDeckSpec(id="deck_1", title="智能体协作", slides=[slide])
    image = ImageElement(id="image_req_1", title="协作流程图", prompt="prompt", asset_url="/asset.png", alt_text="协作流程图")

    page = SlideRenderer().render(deck, [image]).pages[0].page
    ids = [element.id for element in page.elements]
    visual_back = next(element for element in page.elements if element.id == f"{slide.id}_visual_back")
    rendered_image = next(element for element in page.elements if element.id == "image_req_1")
    title = next(element for element in page.elements if element.id == f"{slide.id}_title")

    assert title.width >= 760
    assert visual_back.height >= 320
    assert rendered_image.height >= 280
    assert f"{slide.id}_summary_shape" not in ids


def test_apimart_prompts_match_slide_layout_image_density_rules() -> None:
    image_text_prompt = APIMartImageGenerationService._build_prompt(
        description="展示智能体分工协作。",
        aspect_ratio="4:3",
        layout="image_text",
    )
    visual_summary_prompt = APIMartImageGenerationService._build_prompt(
        description="总结智能体协作流程。",
        aspect_ratio="21:9",
        layout="visual_summary",
    )

    assert "medium-sized right-side panel" in image_text_prompt
    assert "No infographic" in image_text_prompt
    assert "not a full slide" in image_text_prompt
    assert "No title bar" in image_text_prompt
    assert "wide landscape summary diagram" in visual_summary_prompt
    assert "3-5 major nodes" in visual_summary_prompt
    assert "diagram asset" in visual_summary_prompt
    assert "centered safe area" in visual_summary_prompt
    assert "No outer title" in visual_summary_prompt


def test_validator_reports_extra_text_cards_and_prefixed_summaries() -> None:
    state = _state()
    unit = _unit()
    state.outline = type("OutlineStub", (), {"units": [unit]})()  # type: ignore[assignment]
    state.current_unit_spec = SlideSpecPage.model_construct(
        id="slide_unit_1",
        outline_unit_id="unit_1",
        order=1,
        title="智能体协作",
        core_message="智能体通过分工完成复杂任务。",
        layout="visual_summary",
        design_intent="Use a large visual.",
        layout_hints={"supported_renderer": "scenekit.slide/v1"},
        speaker_notes="讲解智能体协作机制。",
        source_chunk_ids=["chunk_1"],
        required_elements=[],
        elements=[
            SlideSpecElement(id="title", type="text", content="智能体协作", metadata={"role": "title"}),
            SlideSpecElement(id="summary", type="text", content="核心点：协作让任务可控", metadata={"role": "summary_text"}),
            SlideSpecElement(id="lead", type="text", content="多余卡片。", metadata={"role": "lead_card", "display_label": "核心解释"}),
            SlideSpecElement(id="visual", type="element_ref", element_id="image_req_1", metadata={"role": "visual"}),
        ],
    )

    report = validate_unit_spec(state)["spec_validation_report"]

    assert report["passed"] is False
    assert any("visual_summary layout has extra text card roles" in error for error in report["errors"])
    assert any("must not include fixed summary prefix" in error for error in report["errors"])
