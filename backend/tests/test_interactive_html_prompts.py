from pathlib import Path

from app.renderers.interactive_html_composer import InteractiveHtmlComposer
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec, InteractiveHtmlTeachingBlock
from app.schemas.specs.interactive_html_style import DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE


PROMPT_ROOT = Path("backend/app/prompts")


def test_interactive_html_outline_prompt_does_not_plan_modules_or_blocks() -> None:
    prompt = (PROMPT_ROOT / "planner" / "interactive_html_outline.md").read_text(encoding="utf-8")

    assert "每个 unit 必须包含 module_type" not in prompt
    assert "module_type 决定" not in prompt
    assert "必须覆盖以下 8 种模块类型" not in prompt
    assert "hero / concept / flow / case" not in prompt
    assert "不指定具体 Block 类型" in prompt


def test_interactive_html_unit_spec_prompt_focuses_on_teaching_design() -> None:
    prompt = (PROMPT_ROOT / "generator" / "interactive_html_unit_spec.md").read_text(encoding="utf-8")

    assert "teaching_flow" in prompt
    assert "InteractiveHtmlTeachingBlock" in prompt
    assert "interaction_specs" in prompt
    assert "禁止输出 HTML" in prompt
    assert "禁止输出 CSS" in prompt or "禁止输出 HTML、CSS" in prompt


def test_interactive_html_unit_render_prompt_generates_explanation_html_and_css() -> None:
    prompt = (PROMPT_ROOT / "generator" / "interactive_html_unit_render.md").read_text(encoding="utf-8")

    assert "block_html_map" in prompt
    assert "css_fragment" in prompt
    assert "style_scope_id" in prompt
    assert "button、input、textarea、form" in prompt
    assert "data-ih-action" in prompt
    assert "data-interaction-id" in prompt
    assert "禁止 html" in prompt or "禁止 <html>" in prompt or "禁止 html、head" in prompt
    assert "禁止 script" in prompt or "禁止 <script>" in prompt
    assert "禁止 onClick" in prompt or "禁止 onclick" in prompt
    assert "CSS 作用域" in prompt


def test_interactive_html_unit_render_prompt_can_be_formatted_with_literal_examples() -> None:
    section_spec = InteractiveHtmlSectionSpec(
        section_id="unit_01",
        title="Unit 01",
        learning_goal="Understand the rendering contract.",
        teaching_flow=[
            InteractiveHtmlTeachingBlock(
                block_id="unit_01_intro",
                block_type="intro",
                title="Intro",
                teaching_role="set_context",
                content_goal="Introduce the unit.",
            )
        ],
    )

    prompt = InteractiveHtmlComposer()._build_render_prompt(
        section_spec=section_spec,
        style_guide=DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE,
        retrieval_context=[],
    )

    assert 'style_scope_id：必须为 "ih-scope-unit_01"' in prompt
    assert "block_html_map" in prompt
    assert '"section_id": "unit_01"' in prompt


def test_interactive_html_render_repair_prompt_guides_repair() -> None:
    prompt = (PROMPT_ROOT / "reviewer" / "interactive_html_render_repair.md").read_text(encoding="utf-8")

    assert "修复" in prompt
    assert "InteractiveHtmlRenderedUnit" in prompt
    assert "校验报告" in prompt
    assert "CSS 作用域" in prompt
