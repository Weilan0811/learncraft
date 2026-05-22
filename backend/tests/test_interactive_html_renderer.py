import pytest

from app.renderers.interactive_html_composer import InteractiveHtmlComposer, InteractiveHtmlRenderError
from app.renderers.interactive_html_explanation_composer import InteractiveHtmlExplanationRender
from app.renderers.interactive_html_interaction_renderer import InteractionTemplateRenderer
from app.renderers.interactive_html_unit_assembler import UnitHtmlAssembler
from app.renderers.interactive_html_renderer import InteractiveHtmlRenderer
from app.schemas.render.interactive_html import InteractionRenderRef, InteractiveHtmlRenderBlockRef, InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlInteractionOption, InteractiveHtmlInteractionSpec, InteractiveHtmlSectionSpec, InteractiveHtmlTeachingBlock
from app.schemas.specs.interactive_html_style import DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE
from app.schemas.state import ContentGenerationState
from app.validators.interactive_html_validator import sanitize_rendered_unit, validate_rendered_unit
import app.workflows.nodes.unit_renderer_node as unit_renderer_node
from app.workflows.nodes.render_unit_repair_node import fallback_render_unit, repair_render_unit
from app.workflows.nodes.unit_renderer_node import render_unit, route_after_render_unit


def _rendered_unit(section_id: str = "unit_1") -> InteractiveHtmlRenderedUnit:
    scope_id = f"ih-scope-{section_id}"
    return InteractiveHtmlRenderedUnit(
        section_id=section_id,
        title="课程导入",
        learning_goal="理解互动课件的结构",
        style_scope_id=scope_id,
        html_fragment=f"""
        <section id="{section_id}" class="ih-unit {scope_id}" data-section-id="{section_id}">
          <article class="ih-block ih-block--intro" data-block-id="{section_id}_intro" data-block-type="intro">
            <h3>课程导入</h3>
            <p>互动课程由讲解、展示和检查点组成。</p>
          </article>
          <article class="ih-block ih-block--concept" data-block-id="{section_id}_concept" data-block-type="concept">
            <h4>课件结构</h4>
            <p>一个单元可以先建立理解，再通过互动诊断关键误区。</p>
          </article>
          <article class="ih-block ih-block--quiz" data-block-id="{section_id}_check" data-block-type="quiz">
            <p>哪种方式更适合前端稳定展示？</p>
            <button data-ih-action="single-choice" data-interaction-id="i_q1" data-option-id="a">让前端稳定渲染组件</button>
          </article>
        </section>
        """,
        css_fragment=f"""
        .{scope_id} {{ max-width: 800px; margin: 0 auto; padding: 24px; }}
        .{scope_id} .ih-block {{ background: #fff; border-radius: 16px; padding: 20px; margin-bottom: 16px; }}
        """,
        block_manifest=[
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_intro", type="intro", title="课程导入", teaching_role="set_context"),
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_concept", type="concept", title="课件结构", teaching_role="explain_core"),
            InteractiveHtmlRenderBlockRef(block_id=f"{section_id}_check", type="quiz", title="结构理解诊断", teaching_role="diagnose_understanding", interaction_ids=["i_q1"]),
        ],
        interaction_manifest=[
            InteractionRenderRef(interaction_id="i_q1", section_id=section_id, type="single_choice", target_concepts=["结构化规格"], event_type="single_choice_answered"),
        ],
    )


def test_interactive_html_renderer_assemble_builds_render_model() -> None:
    rendered_unit = _rendered_unit()
    style_guide = DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE

    model = InteractiveHtmlRenderer().assemble(
        lesson_id="lesson_contract",
        title="互动式课程",
        rendered_units=[rendered_unit],
        style_guide=style_guide,
    )

    assert model.render_type == "interactive_html_page"
    assert model.layout == "vertical_lesson_with_tutor"
    assert model.navigation[0].section_id == "unit_1"
    assert model.navigation[0].anchor == "#unit_1"
    assert model.runtime.progress_tracking is True
    assert model.interactions[0].interaction_id == "i_q1"
    assert model.interactions[0].event_type == "single_choice_answered"
    assert "<section" in model.sections[0].html_fragment
    assert model.sections[0].css_fragment != ""
    assert model.sections[0].style_scope_id == "ih-scope-unit_1"
    assert model.sections[0].block_manifest[2].teaching_role == "diagnose_understanding"
    assert model.style_guide["style_id"] == style_guide.style_id


def test_interactive_html_renderer_assemble_multiple_units() -> None:
    unit_1 = _rendered_unit("unit_1")
    unit_2 = _rendered_unit("unit_2")
    style_guide = DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE

    model = InteractiveHtmlRenderer().assemble(
        lesson_id="lesson_multi",
        title="多单元课程",
        rendered_units=[unit_1, unit_2],
        style_guide=style_guide,
    )

    assert len(model.sections) == 2
    assert len(model.navigation) == 2
    assert model.navigation[0].section_id == "unit_1"
    assert model.navigation[1].section_id == "unit_2"
    assert len(model.interactions) == 2


def test_interaction_template_renderer_outputs_four_p0_contracts() -> None:
    section = InteractiveHtmlSectionSpec(
        section_id="unit_1",
        title="模板协议",
        learning_goal="验证四类互动协议",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(block_id="unit_1_sc", block_type="single_choice", title="单选", teaching_role="diagnose", content_goal="单选", interaction_id="i_sc"),
            InteractiveHtmlTeachingBlock(block_id="unit_1_mc", block_type="multiple_choice", title="多选", teaching_role="diagnose", content_goal="多选", interaction_id="i_mc"),
            InteractiveHtmlTeachingBlock(block_id="unit_1_sa", block_type="short_answer", title="简答", teaching_role="reflect", content_goal="简答", interaction_id="i_sa"),
            InteractiveHtmlTeachingBlock(block_id="unit_1_sd", block_type="scenario_discussion", title="情景", teaching_role="transfer", content_goal="情景", interaction_id="i_sd"),
        ],
        interaction_specs=[
            InteractiveHtmlInteractionSpec(
                interaction_id="i_sc",
                block_id="unit_1_sc",
                type="single_choice",
                event_type="single_choice_answered",
                prompt="单选题",
                options=[InteractiveHtmlInteractionOption(id=str(i), text=f"选项 {i}", is_correct=i == 1, feedback="反馈") for i in range(1, 5)],
            ),
            InteractiveHtmlInteractionSpec(
                interaction_id="i_mc",
                block_id="unit_1_mc",
                type="multiple_choice",
                event_type="multiple_choice_answered",
                prompt="多选题",
                options=[InteractiveHtmlInteractionOption(id=str(i), text=f"选项 {i}", is_correct=i in {1, 2}, feedback="反馈") for i in range(1, 5)],
            ),
            InteractiveHtmlInteractionSpec(
                interaction_id="i_sa",
                block_id="unit_1_sa",
                type="short_answer",
                event_type="short_answer_submitted",
                prompt="简答题",
                placeholder="请输入",
                reference_points=["协议稳定"],
                min_length=10,
            ),
            InteractiveHtmlInteractionSpec(
                interaction_id="i_sd",
                block_id="unit_1_sd",
                type="scenario_discussion",
                event_type="scenario_discussion_submitted",
                prompt="讨论题",
                placeholder="请输入",
                reference_points=["模板生成"],
                min_length=12,
                scenario={"background": "背景", "task": "任务"},
            ),
        ],
    )

    rendered = InteractionTemplateRenderer().render(section, "ih-scope-unit_1")
    html = "\n".join(block.html_fragment for block in rendered.values())

    assert 'data-ih-action="single-choice"' in html
    assert 'data-ih-action="multiple-choice-toggle"' in html
    assert 'data-ih-action="multiple-choice-submit"' in html
    assert 'data-ih-action="short-answer-submit"' in html
    assert 'data-ih-action="scenario-discussion-submit"' in html
    assert 'data-ih-input-for="i_sa"' in html
    assert 'data-reference-points="协议稳定"' in html


def test_unit_assembler_preserves_teaching_flow_order_and_fallback() -> None:
    section = _section_spec()
    explanation = InteractiveHtmlExplanationRender(
        section_id="unit_1",
        style_scope_id="ih-scope-unit_1",
        block_html_map={
            "unit_1_intro": '<article class="ih-block" data-block-id="unit_1_intro" data-block-type="intro"><h3>导入</h3><p>第一段。</p></article>'
        },
        css_fragment=".ih-scope-unit_1 { overflow-wrap: break-word; }",
    )

    unit = UnitHtmlAssembler().assemble(section, explanation, {}, "ih-scope-unit_1")

    assert unit.html_fragment.index('data-block-id="unit_1_intro"') < unit.html_fragment.index('data-block-id="unit_1_concept"')
    assert "ih-warning" in unit.html_fragment
    assert unit.render_notes["missing_blocks"] == ["unit_1_concept", "unit_1_reflection"]


def test_unit_assembler_does_not_duplicate_frontend_section_header() -> None:
    section = _section_spec()
    explanation = InteractiveHtmlExplanationRender(
        section_id="unit_1",
        style_scope_id="ih-scope-unit_1",
        block_html_map={
            "unit_1_intro": '<article class="ih-block" data-block-id="unit_1_intro" data-block-type="intro"><h3>导入</h3><p>第一段。</p></article>',
            "unit_1_concept": '<article class="ih-block" data-block-id="unit_1_concept" data-block-type="concept_explanation"><h3>核心概念</h3><p>第二段。</p></article>',
            "unit_1_reflection": '<article class="ih-block" data-block-id="unit_1_reflection" data-block-type="reflection"><h3>学习反思</h3><p>第三段。</p></article>',
        },
        css_fragment=".ih-scope-unit_1 { overflow-wrap: break-word; }",
    )

    unit = UnitHtmlAssembler().assemble(section, explanation, {}, "ih-scope-unit_1")

    assert f"<h2>{section.title}</h2>" not in unit.html_fragment
    assert f"<p>{section.learning_goal}</p>" not in unit.html_fragment
    assert unit.html_fragment.count('data-block-id="unit_1_intro"') == 1


def test_composer_falls_back_when_explanation_llm_times_out() -> None:
    class TimeoutExplanationComposer:
        def compose(self, section_spec, style_guide, style_scope_id, retrieval_context=None):
            raise RuntimeError("LLM request failed after retries: ReadTimeout: The read operation timed out")

    composer = InteractiveHtmlComposer(explanation_composer=TimeoutExplanationComposer())

    unit = composer.compose_unit(_section_spec(), DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE)

    assert unit.section_id == "unit_1"
    assert unit.render_notes["fallback"] is True
    assert "LLM request failed after retries" in unit.render_notes["explanation_error"]
    assert validate_rendered_unit(unit).ok is True


def _section_spec(section_id: str = "unit_1") -> InteractiveHtmlSectionSpec:
    return InteractiveHtmlSectionSpec(
        section_id=section_id,
        title="课程导入",
        learning_goal="理解互动课件的结构",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_intro",
                block_type="intro",
                title="课程导入",
                teaching_role="set_context",
                content_goal="建立学习背景",
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_concept",
                block_type="concept_explanation",
                title="核心概念讲解",
                teaching_role="explain_core",
                content_goal="解释核心概念",
            ),
            InteractiveHtmlTeachingBlock(
                block_id=f"{section_id}_reflection",
                block_type="reflection",
                title="学习反思",
                teaching_role="prompt_reflection",
                content_goal="迁移理解",
            ),
        ],
    )


def test_render_unit_routes_interactive_html_llm_failure_to_repair(monkeypatch) -> None:
    def failing_compose(*args, **kwargs):
        raise RuntimeError("LLM returned []")

    monkeypatch.setattr(unit_renderer_node.InteractiveHtmlComposer, "compose_unit", failing_compose)
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        normalized_request={"allow_fallback": False},
    )

    result = render_unit(state)
    next_state = state.model_copy(update=result)

    assert "render_unit failed: LLM returned []" in result["errors"]
    assert route_after_render_unit(next_state) == "repair"


def test_render_unit_routes_read_timeout_to_render_retry_before_repair(monkeypatch) -> None:
    def failing_compose(*args, **kwargs):
        raise RuntimeError("LLM request failed after retries: ReadTimeout: The read operation timed out")

    monkeypatch.setattr(unit_renderer_node.InteractiveHtmlComposer, "compose_unit", failing_compose)
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        normalized_request={"allow_fallback": False},
    )

    result = render_unit(state)
    next_state = state.model_copy(update=result)

    assert result["retry_counts"]["render_unit_transport:unit_1"] == 1
    assert route_after_render_unit(next_state) == "retry"


def test_failed_interactive_render_routes_to_fallback_only_after_repair_when_allowed() -> None:
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        normalized_request={"allow_fallback": True},
        errors=["render_unit failed: still invalid"],
        retry_counts={"render_unit_repair:unit_1": 1},
    )
    strict_state = state.model_copy(update={"normalized_request": {"allow_fallback": False}})

    assert route_after_render_unit(state) == "fallback"
    assert route_after_render_unit(strict_state) == "fail"


def test_exhausted_render_timeout_does_not_route_to_content_repair() -> None:
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        normalized_request={"allow_fallback": False},
        errors=["render_unit failed: LLM request failed after retries: ReadTimeout: The read operation timed out"],
        retry_counts={"render_unit_transport:unit_1": 2},
    )
    fallback_state = state.model_copy(update={"normalized_request": {"allow_fallback": True}})

    assert route_after_render_unit(state) == "fail"
    assert route_after_render_unit(fallback_state) == "fallback"


def test_sanitize_rendered_unit_normalizes_common_action_aliases() -> None:
    unit = _rendered_unit().model_copy(update={
        "html_fragment": """
        <section id="unit_1" class="ih-unit ih-scope-unit_1" data-section-id="unit_1">
          <article data-block-id="unit_1_intro" data-block-type="intro">
            <h3>课程导入</h3>
            <p>互动课程由讲解、展示和检查点组成。</p>
          </article>
          <article data-block-id="unit_1_check" data-block-type="quiz">
            <p>请选择正确答案。</p>
            <button data-ih-action="toggle_selection" data-interaction-id="i_q1" data-option-id="a">A</button>
            <button data-ih-action="check_answer" data-interaction-id="i_q1" data-option-id="submit">提交</button>
          </article>
        </section>
        """,
        "block_manifest": [
            InteractiveHtmlRenderBlockRef(block_id="unit_1_intro", type="intro", title="课程导入", teaching_role="set_context"),
            InteractiveHtmlRenderBlockRef(block_id="unit_1_check", type="quiz", title="检查", teaching_role="diagnose_understanding", interaction_ids=["i_q1"]),
        ],
    })

    sanitized = sanitize_rendered_unit(unit)
    report = validate_rendered_unit(sanitized)

    assert 'data-ih-action="multiple-choice-toggle"' in sanitized.html_fragment
    assert 'data-ih-action="single-choice"' in sanitized.html_fragment
    assert not [issue.message for issue in report.issues if "unsupported data-ih-action" in issue.message]


def test_composer_raises_when_assembled_unit_fails_validation(monkeypatch) -> None:
    from app.renderers.interactive_html_explanation_composer import InteractiveHtmlExplanationRender

    class BadAssembler:
        def assemble(self, section_spec, explanation_render, interaction_blocks, style_scope_id):
            return _rendered_unit(section_spec.section_id).model_copy(update={"html_fragment": "<div>bad</div>"})

    class StubExplanationComposer:
        def compose(self, section_spec, style_guide, style_scope_id, retrieval_context=None):
            return InteractiveHtmlExplanationRender(
                section_id=section_spec.section_id,
                style_scope_id=style_scope_id,
                block_html_map={},
                css_fragment=f".{style_scope_id} {{ overflow-wrap: break-word; }}",
            )

    composer = InteractiveHtmlComposer(explanation_composer=StubExplanationComposer(), unit_assembler=BadAssembler())

    with pytest.raises(InteractiveHtmlRenderError, match="failed validation"):
        composer.compose_unit(_section_spec(), DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE)


def test_render_repair_prompt_includes_allowed_action_contract() -> None:
    invalid_unit = _rendered_unit().model_copy(update={
        "html_fragment": _rendered_unit().html_fragment.replace("single-choice", "check_answer")
    })
    report = validate_rendered_unit(invalid_unit)

    prompt = InteractiveHtmlComposer()._build_repair_prompt(
        invalid_unit,
        report,
        _section_spec(),
        DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE,
    )

    assert "允许的 data-ih-action" in prompt
    assert "single-choice" in prompt
    assert "check_answer -> single-choice" in prompt


def test_repair_render_unit_uses_llm_repair_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_compose(self, section_spec, style_guide, retrieval_context=None, repair_context=None):
        captured["repair_context"] = repair_context
        return _rendered_unit(section_spec.section_id)

    monkeypatch.setattr(unit_renderer_node.InteractiveHtmlComposer, "compose_unit", fake_compose)
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        errors=["render_unit failed: LLM returned []"],
    )

    result = repair_render_unit(state)

    assert captured["repair_context"] == {"errors": ["render_unit failed: LLM returned []"]}
    assert result["render_units"]["unit_1"].status == "rendered"
    assert result["errors"] == []
    assert result["retry_counts"]["render_unit_repair:unit_1"] == 1


def test_fallback_render_unit_builds_interactive_html_snapshot() -> None:
    state = ContentGenerationState(
        request_id="task_1",
        content_type="interactive_html",
        topic="互动课",
        user_prompt="生成课程",
        current_unit_id="unit_1",
        current_unit_spec=_section_spec(),
        errors=["render_unit failed: still invalid"],
    )

    result = fallback_render_unit(state)

    snapshot = result["render_units"]["unit_1"]
    assert snapshot.status == "rendered"
    assert snapshot.render_fragment["section_id"] == "unit_1"
    assert result["errors"] == []
