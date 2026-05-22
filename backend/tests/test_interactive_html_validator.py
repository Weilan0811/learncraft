import pytest

from app.schemas.outline import Outline, OutlineUnit
from app.schemas.render.interactive_html import InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import (
    InteractiveHtmlInteractionOption,
    InteractiveHtmlInteractionSpec,
    InteractiveHtmlMeta,
    InteractiveHtmlSectionSpec,
    InteractiveHtmlSpec,
    InteractiveHtmlTeachingBlock,
)
from app.schemas.state import ContentGenerationState
from app.validators.interactive_html_validator import (
    sanitize_html_fragment,
    sanitize_rendered_unit,
    validate_content,
    validate_rendered_unit,
    validate_unit_spec,
)
import app.workflows.nodes.unit_spec_repair_node as unit_spec_repair_node
from app.workflows.nodes.unit_spec_repair_node import fallback_unit_spec, repair_unit_spec
from app.workflows.nodes.validator_node import route_after_unit_spec_validation
from app.workflows.nodes.validator_node import validate_content as workflow_validate_content
from app.workflows.nodes.validator_node import validate_unit_spec as workflow_validate_unit_spec


def _teaching_block(block_id: str = "unit_1_intro", block_type: str = "intro", interaction_id: str | None = None) -> InteractiveHtmlTeachingBlock:
    return InteractiveHtmlTeachingBlock(
        block_id=block_id,
        block_type=block_type,
        title="检索增强生成的可靠性" if block_type == "intro" else "核心概念讲解" if block_type == "concept_explanation" else "理解诊断",
        teaching_role="set_context" if block_type == "intro" else "explain_core" if block_type == "concept_explanation" else "diagnose_understanding",
        content_goal="理解检索增强生成的核心原理",
        must_cover=["检索增强生成的基本流程"],
        interaction_id=interaction_id,
    )


def _interaction_spec(interaction_id: str = "unit_1_q1", block_id: str = "unit_1_check") -> InteractiveHtmlInteractionSpec:
    return InteractiveHtmlInteractionSpec(
        interaction_id=interaction_id,
        block_id=block_id,
        type="single_choice",
        event_type="single_choice_answered",
        target_concepts=["引用来源"],
        prompt="引用来源的主要价值是什么？",
        options=[
            InteractiveHtmlInteractionOption(id="a", text="便于追溯依据", is_correct=True, feedback="正确。引用来源让内容可追溯。"),
            InteractiveHtmlInteractionOption(id="b", text="增加页面美观", is_correct=False, feedback="不对。美观不是引用来源的主要价值。"),
            InteractiveHtmlInteractionOption(id="c", text="隐藏生成过程", is_correct=False, feedback="不对。引用来源提升透明度。"),
            InteractiveHtmlInteractionOption(id="d", text="减少所有交互", is_correct=False, feedback="不对。引用来源与交互数量无关。"),
        ],
    )


def _valid_section(section_id: str = "unit_1") -> InteractiveHtmlSectionSpec:
    return InteractiveHtmlSectionSpec(
        section_id=section_id,
        title="检索增强生成的可靠性",
        learning_goal="理解引用来源如何提升生成内容的可靠性",
        narrative_goal="从检索增强生成的基本流程出发，理解引用来源的价值",
        teaching_flow=[
            _teaching_block(f"{section_id}_intro", "intro"),
            _teaching_block(f"{section_id}_concept", "concept_explanation"),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_check",
                block_type="single_choice",
                title="引用来源的价值诊断",
                teaching_role="diagnose_understanding",
                content_goal="诊断对引用来源价值的理解",
                must_cover=["引用来源的价值"],
                interaction_id="unit_1_q1",
            ),
            _teaching_block(f"{section_id}_reflection", "reflection"),
        ],
        interaction_specs=[_interaction_spec(block_id=f"{section_id}_check")],
    )


def _valid_spec(section: InteractiveHtmlSectionSpec | None = None) -> InteractiveHtmlSpec:
    return InteractiveHtmlSpec(
        lesson_id="lesson_1",
        title="互动式生成课程",
        meta=InteractiveHtmlMeta(audience="产品和教学设计人员"),
        sections=[section or _valid_section()],
    )


def _rendered_html(section_id: str = "unit_1", interaction_id: str = "unit_1_q1") -> str:
    scope_id = f"ih-scope-{section_id}"
    return f"""
    <section id="{section_id}" class="ih-unit {scope_id}" data-section-id="{section_id}">
      <div class="ih-eyebrow">知识点讲解</div>
      <article class="ih-block ih-block--intro" data-block-id="{section_id}_intro" data-block-type="intro">
        <h3>检索增强生成的可靠性</h3>
        <p>检索增强生成会先从知识库中找到相关材料，再把材料交给模型组织成回答。</p>
      </article>
      <article class="ih-block ih-block--concept" data-block-id="{section_id}_concept" data-block-type="concept">
        <h4>为什么引用来源重要？</h4>
        <p>引用来源能帮助学习者判断内容依据，也能让系统输出更可验证。</p>
        <div class="ih-card">引用让内容从"看起来合理"变成"可以追溯和复核"。</div>
      </article>
      <article class="ih-block ih-block--quiz" data-block-id="{section_id}_check" data-block-type="quiz">
        <p>现在判断一个关键误区：引用来源的主要价值是什么？</p>
        <button class="ih-btn ih-btn--primary" data-ih-action="single-choice" data-interaction-id="{interaction_id}" data-option-id="a">便于追溯依据</button>
      </article>
    </section>
    """


def _rendered_css(section_id: str = "unit_1") -> str:
    scope_id = f"ih-scope-{section_id}"
    return f"""
    .{scope_id} {{
      --ih-accent: #5b6cff;
      --ih-surface: #ffffff;
      max-width: 800px;
      margin: 0 auto;
      padding: 24px;
      overflow-wrap: break-word;
    }}
    .{scope_id} .ih-block {{
      background: var(--ih-surface);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 16px;
    }}
    """


def _valid_rendered_unit(section_id: str = "unit_1") -> InteractiveHtmlRenderedUnit:
    from app.schemas.render.interactive_html import InteractionRenderRef, InteractiveHtmlRenderBlockRef
    scope_id = f"ih-scope-{section_id}"
    return InteractiveHtmlRenderedUnit(
        section_id=section_id,
        title="检索增强生成的可靠性",
        learning_goal="理解引用来源如何提升生成内容的可靠性",
        style_scope_id=scope_id,
        html_fragment=_rendered_html(section_id),
        css_fragment=_rendered_css(section_id),
        block_manifest=[
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_intro", type="intro", title="检索增强生成的可靠性", teaching_role="set_context"),
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_concept", type="concept", title="为什么引用来源重要", teaching_role="explain_core"),
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_check", type="quiz", title="引用来源的价值诊断", teaching_role="diagnose_understanding", interaction_ids=["unit_1_q1"]),
        ],
        interaction_manifest=[
            InteractionRenderRef(interaction_id="unit_1_q1", section_id=section_id, type="single_choice", target_concepts=["引用来源"], event_type="single_choice_answered"),
        ],
    )


def test_unit_spec_schema_accepts_teaching_flow_and_interaction_specs() -> None:
    section = _valid_section()

    assert section.teaching_flow[0].block_type == "intro"
    assert section.teaching_flow[0].teaching_role == "set_context"
    assert section.interaction_specs[0].event_type == "single_choice_answered"
    assert section.interaction_specs[0].prompt is not None


def test_validate_unit_spec_accepts_valid_section() -> None:
    report = validate_unit_spec(_valid_section())

    assert report.ok is True
    assert report.issues == []


def test_validate_unit_spec_rejects_missing_fields() -> None:
    section = InteractiveHtmlSectionSpec(
        section_id="",
        title="",
        learning_goal="",
        teaching_flow=[],
        interaction_specs=[],
    )

    report = validate_unit_spec(section)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("section_id is missing" in m for m in messages)
    assert any("title is missing" in m for m in messages)
    assert any("learning_goal is missing" in m for m in messages)
    assert any("teaching_flow should contain 3-7 teaching blocks" in m for m in messages)


def test_validate_unit_spec_rejects_duplicate_block_ids() -> None:
    section = InteractiveHtmlSectionSpec(
        section_id="unit_1",
        title="测试",
        learning_goal="测试重复 block_id",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(block_id="dup_1", block_type="intro", title="标题一", teaching_role="set_context", content_goal="目标一"),
            InteractiveHtmlTeachingBlock(block_id="dup_1", block_type="concept_explanation", title="标题二", teaching_role="explain_core", content_goal="目标二"),
            InteractiveHtmlTeachingBlock(block_id="dup_2", block_type="summary", title="总结", teaching_role="wrap_up", content_goal="收束"),
        ],
        interaction_specs=[],
    )

    report = validate_unit_spec(section)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("block_id values must be unique" in m for m in messages)


def test_validate_unit_spec_rejects_interaction_spec_with_invalid_block_id() -> None:
    section = InteractiveHtmlSectionSpec(
        section_id="unit_1",
        title="测试",
        learning_goal="测试无效 block_id 引用",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(block_id="b1", block_type="intro", title="导入", teaching_role="set_context", content_goal="导入目标"),
            InteractiveHtmlTeachingBlock(block_id="b2", block_type="concept_explanation", title="讲解", teaching_role="explain_core", content_goal="讲解目标"),
            InteractiveHtmlTeachingBlock(block_id="b3", block_type="summary", title="总结", teaching_role="wrap_up", content_goal="收束"),
        ],
        interaction_specs=[
            InteractiveHtmlInteractionSpec(
                interaction_id="i1",
                block_id="nonexistent_block",
                type="single_choice",
                event_type="single_choice_answered",
            )
        ],
    )

    report = validate_unit_spec(section)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("does not exist in teaching_flow" in m for m in messages)


def test_validate_unit_spec_enforces_p0_interaction_contracts() -> None:
    section = _valid_section().model_copy(update={
        "interaction_specs": [
            InteractiveHtmlInteractionSpec(
                interaction_id="bad_mc",
                block_id="unit_1_check",
                type="multiple_choice",
                event_type="single_choice_answered",
                prompt="哪些做法正确？",
                options=[
                    InteractiveHtmlInteractionOption(id="a", text="A", is_correct=False, feedback="不对"),
                    InteractiveHtmlInteractionOption(id="b", text="B", is_correct=False, feedback="不对"),
                    InteractiveHtmlInteractionOption(id="c", text="C", is_correct=False, feedback="不对"),
                    InteractiveHtmlInteractionOption(id="d", text="D", is_correct=False, feedback="不对"),
                ],
            )
        ]
    })

    report = validate_unit_spec(section)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("multiple_choice event_type must be multiple_choice_answered" in m for m in messages)
    assert any("multiple_choice requires at least one correct option" in m for m in messages)


def test_validate_unit_spec_accepts_short_answer_and_scenario_discussion() -> None:
    section = _valid_section().model_copy(update={
        "teaching_flow": [
            _teaching_block("unit_1_intro", "intro"),
            _teaching_block("unit_1_concept", "concept_explanation"),
            InteractiveHtmlTeachingBlock(
                block_id="unit_1_sa",
                block_type="short_answer",
                title="解释协议稳定性",
                teaching_role="prompt_reflection",
                content_goal="解释为什么互动模板更稳定",
                interaction_id="unit_1_i_sa",
            ),
            InteractiveHtmlTeachingBlock(
                block_id="unit_1_sd",
                block_type="scenario_discussion",
                title="设计方案讨论",
                teaching_role="transfer",
                content_goal="在真实情境中选择渲染策略",
                interaction_id="unit_1_i_sd",
            ),
        ],
        "interaction_specs": [
            InteractiveHtmlInteractionSpec(
                interaction_id="unit_1_i_sa",
                block_id="unit_1_sa",
                type="short_answer",
                event_type="short_answer_submitted",
                prompt="请解释模板化互动的价值。",
                placeholder="写下你的解释",
                reference_points=["协议稳定", "事件可追踪"],
                min_length=12,
            ),
            InteractiveHtmlInteractionSpec(
                interaction_id="unit_1_i_sd",
                block_id="unit_1_sd",
                type="scenario_discussion",
                event_type="scenario_discussion_submitted",
                prompt="你会选择哪种方案？",
                placeholder="我会选择……",
                reference_points=["讲解由 LLM 生成", "互动由模板生成"],
                min_length=20,
                scenario={"background": "需要同时保证美观和稳定。", "task": "选择互动渲染方案并说明理由。"},
            ),
        ],
    })

    report = validate_unit_spec(section)

    assert report.ok is True


def test_validate_rendered_unit_accepts_valid_unit() -> None:
    report = validate_rendered_unit(_valid_rendered_unit())

    assert report.ok is True
    assert report.issues == []


def test_validate_rendered_unit_rejects_missing_css() -> None:
    unit = _valid_rendered_unit()
    unit = unit.model_copy(update={"css_fragment": ""})

    report = validate_rendered_unit(unit)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("css_fragment is missing" in m for m in messages)


def test_validate_rendered_unit_rejects_unscoped_css() -> None:
    unit = _valid_rendered_unit()
    unit = unit.model_copy(update={"css_fragment": "body { color: red; }"})

    report = validate_rendered_unit(unit)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("global selectors" in m for m in messages)


def test_validate_rendered_unit_rejects_css_import() -> None:
    unit = _valid_rendered_unit()
    css = unit.css_fragment + "\n@import url('https://evil.com/style.css');"
    unit = unit.model_copy(update={"css_fragment": css})

    report = validate_rendered_unit(unit)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("@import" in m for m in messages)


def test_validate_rendered_unit_rejects_manifest_mismatch() -> None:
    unit = _valid_rendered_unit()
    unit = unit.model_copy(update={"block_manifest": []})

    report = validate_rendered_unit(unit)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("block_manifest must match" in m for m in messages)


def test_validate_rendered_unit_rejects_missing_style_scope_in_html() -> None:
    html = '<section id="unit_1" class="ih-unit" data-section-id="unit_1"><h3>标题</h3><p>正文</p></section>'
    unit = _valid_rendered_unit()
    unit = unit.model_copy(update={"html_fragment": html})

    report = validate_rendered_unit(unit)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("style_scope_id" in m for m in messages)


def test_sanitize_html_fragment_removes_scripts_handlers_and_unsafe_urls() -> None:
    dirty = """
    <section id="unit_1" class="ih-unit" onclick="alert(1)">
      <script>alert(1)</script>
      <p><a href="javascript:alert(1)" data-ih-action="x">坏链接</a></p>
      <button class="ih-btn" data-ih-action="single-choice" data-interaction-id="q1" data-option-id="a">选择</button>
    </section>
    """

    clean = sanitize_html_fragment(dirty)

    assert "<script" not in clean
    assert "onclick" not in clean
    assert "javascript:" not in clean
    assert 'class="ih-btn"' in clean
    assert 'data-ih-action="single-choice"' in clean
    assert 'data-interaction-id="q1"' in clean


def test_sanitize_rendered_unit_cleans_html_and_css() -> None:
    unit = InteractiveHtmlRenderedUnit(
        section_id="unit_1",
        title="测试",
        learning_goal="测试清洗",
        style_scope_id="ih-scope-unit_1",
        html_fragment='<section id="unit_1" class="ih-unit ih-scope-unit_1" data-section-id="unit_1"><script>alert(1)</script><h3>标题</h3><p>正文</p></section>',
        css_fragment=".ih-scope-unit_1 { color: red; }\n@import url('https://evil.com/style.css');",
    )

    sanitized = sanitize_rendered_unit(unit)

    assert "<script" not in sanitized.html_fragment
    assert "@import" not in sanitized.css_fragment


def test_validate_content_accepts_valid_spec() -> None:
    report = validate_content(_valid_spec())

    assert report.ok is True
    assert report.issues == []


def test_validate_content_rejects_empty_sections() -> None:
    spec = InteractiveHtmlSpec(
        lesson_id="lesson_1",
        title="空课程",
        meta=InteractiveHtmlMeta(audience="general"),
        sections=[],
    )

    report = validate_content(spec)

    assert report.ok is False
    messages = [issue.message for issue in report.issues]
    assert any("at least one section" in m for m in messages)


def test_workflow_validator_uses_interactive_html_validator_for_unit_and_content() -> None:
    bad_section = InteractiveHtmlSectionSpec(
        section_id="unit_1",
        title="",
        learning_goal="",
        teaching_flow=[],
        interaction_specs=[],
    )
    outline = Outline(
        id="outline_1",
        content_type="interactive_html",
        title="互动课",
        units=[
            OutlineUnit(
                id="unit_1",
                order=1,
                unit_type="interactive_section",
                title="错误片段",
                goal="阻止不合规 spec 进入渲染",
                core_message="Spec 校验需要检查必填字段。",
                retrieval_queries=["互动课质量"],
            )
        ],
    )
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        outline=outline,
        pending_unit_ids=["unit_1"],
        current_unit_id="unit_1",
        current_unit_spec=bad_section,
        content_spec=_valid_spec(bad_section),
    )

    unit_result = workflow_validate_unit_spec(state)
    content_result = workflow_validate_content(state)

    assert unit_result["spec_validation_report"]["passed"] is False
    assert content_result["validation_report"]["passed"] is False


def test_failed_unit_spec_validation_routes_to_repair_before_fail() -> None:
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        spec_validation_report={"passed": False, "errors": ["unit_spec.section_id does not match current unit"]},
        retry_counts={},
    )

    assert route_after_unit_spec_validation(state) == "repair"


def test_repair_unit_spec_uses_llm_repair_with_validation_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_section = InteractiveHtmlSectionSpec(
        section_id="sec_001",
        title="Sample Section",
        learning_goal="Acquire fundamental knowledge",
        teaching_flow=[],
        interaction_specs=[],
    )
    outline = Outline(
        id="outline_1",
        content_type="interactive_html",
        title="互动课",
        units=[
            OutlineUnit(
                id="unit_1",
                order=1,
                unit_type="interactive_section",
                title="多模态基础",
                goal="理解多模态大模型的基本结构",
                core_message="多模态系统通过统一语义空间连接文本、图像和音频。",
                key_points=["统一表征", "跨模态对齐", "互补推理"],
                retrieval_queries=["多模态大模型基础"],
            )
        ],
    )
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        outline=outline,
        pending_unit_ids=["unit_1"],
        current_unit_id="unit_1",
        current_unit_spec=bad_section,
        spec_validation_report={
            "passed": False,
            "errors": [
                "unit_spec.section_id does not match current unit",
                "teaching_flow: teaching_flow should contain 3-7 teaching blocks",
            ],
        },
        errors=[
            "unit_spec.section_id does not match current unit",
            "teaching_flow: teaching_flow should contain 3-7 teaching blocks",
        ],
    )

    captured: dict[str, object] = {}

    def fake_repair(repair_state: ContentGenerationState, repair_unit: OutlineUnit, chunk_ids: list[str], errors: list[str]):
        captured["unit_id"] = repair_unit.id
        captured["errors"] = errors
        return _valid_section("unit_1")

    monkeypatch.setattr(unit_spec_repair_node, "repair_unit_spec_with_llm", fake_repair)

    result = repair_unit_spec(state)
    repaired = result["current_unit_spec"]

    assert repaired.section_id == "unit_1"
    assert captured["unit_id"] == "unit_1"
    assert captured["errors"] == [
        "unit_spec.section_id does not match current unit",
        "teaching_flow: teaching_flow should contain 3-7 teaching blocks",
    ]
    assert 3 <= len(repaired.teaching_flow) <= 7
    assert result["errors"] == []
    assert result["retry_counts"]["unit_spec_repair:unit_1"] == 1


def test_failed_repaired_unit_spec_routes_to_fallback_only_when_allowed() -> None:
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        normalized_request={"allow_fallback": True},
        current_unit_id="unit_1",
        spec_validation_report={"passed": False, "errors": ["still invalid"]},
        retry_counts={"unit_spec_repair:unit_1": 1},
    )
    strict_state = state.model_copy(update={"normalized_request": {"allow_fallback": False}})

    assert route_after_unit_spec_validation(state) == "fallback"
    assert route_after_unit_spec_validation(strict_state) == "fail"


def test_fallback_unit_spec_is_explicit_last_resort() -> None:
    outline = Outline(
        id="outline_1",
        content_type="interactive_html",
        title="互动课",
        units=[
            OutlineUnit(
                id="unit_1",
                order=1,
                unit_type="interactive_section",
                title="多模态基础",
                goal="理解多模态大模型的基本结构",
                core_message="多模态系统通过统一语义空间连接文本、图像和音频。",
                key_points=["统一表征", "跨模态对齐", "互补推理"],
                retrieval_queries=["多模态大模型基础"],
            )
        ],
    )
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        outline=outline,
        pending_unit_ids=["unit_1"],
        current_unit_id="unit_1",
        spec_validation_report={"passed": False, "errors": ["still invalid"]},
        errors=["still invalid"],
    )

    result = fallback_unit_spec(state)
    fallback = result["current_unit_spec"]

    assert fallback.section_id == "unit_1"
    assert fallback.title == "多模态基础"
    assert result["errors"] == []
