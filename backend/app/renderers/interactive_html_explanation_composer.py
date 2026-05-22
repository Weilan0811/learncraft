import json
import os
from html import escape
from typing import cast

from pydantic import Field

from app.schemas.base import SchemaModel
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
from app.schemas.specs.interactive_html_style import InteractiveHtmlCourseStyleGuide
from app.services.llm_service import get_llm_service
from app.validators.interactive_html_validator import validate_explanation_render


INTERACTION_BLOCK_TYPES = {"single_choice", "multiple_choice", "short_answer", "scenario_discussion"}


class InteractiveHtmlExplanationRender(SchemaModel):
    section_id: str
    style_scope_id: str
    block_html_map: dict[str, str] = Field(default_factory=dict)
    css_fragment: str
    render_notes: dict = Field(default_factory=dict)


class ExplanationHtmlComposer:
    def compose(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        style_scope_id: str,
        retrieval_context: list | None = None,
    ) -> InteractiveHtmlExplanationRender:
        interaction_block_ids = {spec.block_id for spec in section_spec.interaction_specs}
        explanation_spec = section_spec.model_copy(
            update={
                "teaching_flow": [
                    block for block in section_spec.teaching_flow
                    if block.block_type not in INTERACTION_BLOCK_TYPES
                    and block.block_id not in interaction_block_ids
                ],
                "interaction_specs": [],
            }
        )
        if not explanation_spec.teaching_flow:
            return InteractiveHtmlExplanationRender(
                section_id=section_spec.section_id,
                style_scope_id=style_scope_id,
                block_html_map={},
                css_fragment=self._fallback_css(style_scope_id, style_guide),
                render_notes={"empty_explanation": True},
            )

        prompt = self._build_render_prompt(explanation_spec, style_guide, style_scope_id, retrieval_context)
        llm_service = get_llm_service()
        rendered = cast(
            InteractiveHtmlExplanationRender,
            llm_service.generate_structured(prompt=prompt, schema=InteractiveHtmlExplanationRender),
        )
        report = validate_explanation_render(rendered.block_html_map, rendered.css_fragment, style_scope_id)
        if report.ok:
            return rendered

        # Keep the interaction contract stable even when the LLM explanation render fails.
        return InteractiveHtmlExplanationRender(
            section_id=section_spec.section_id,
            style_scope_id=style_scope_id,
            block_html_map={
                block.block_id: self._fallback_block(block.block_id, block.title, block.content_goal)
                for block in explanation_spec.teaching_flow
            },
            css_fragment=self._fallback_css(style_scope_id, style_guide),
            render_notes={
                "fallback": True,
                "validation_errors": [f"{issue.path}: {issue.message}" for issue in report.issues],
            },
        )

    def _build_render_prompt(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        style_scope_id: str,
        retrieval_context: list | None = None,
    ) -> str:
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "generator", "interactive_html_unit_render.md"
        )
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        retrieval_text = ""
        if retrieval_context:
            retrieval_text = json.dumps(
                [chunk.model_dump() if hasattr(chunk, "model_dump") else chunk for chunk in retrieval_context],
                ensure_ascii=False,
                indent=2,
            )

        return template.format(
            unit_spec=section_spec.model_dump_json(indent=2),
            style_guide=style_guide.model_dump_json(indent=2),
            style_scope_id=style_scope_id,
            runtime_contract=json.dumps({
                "forbidden_in_explanation": [
                    "button", "input", "textarea", "form", "data-ih-action",
                    "data-interaction-id", "script", "inline event handlers",
                ],
            }, ensure_ascii=False, indent=2),
            retrieval_context=retrieval_text or "无",
        )

    def _fallback_block(self, block_id: str, title: str, content_goal: str) -> str:
        return (
            f'<article class="ih-block ih-explanation-fallback" data-block-id="{escape(block_id)}" '
            f'data-block-type="concept_explanation"><h3>{escape(title)}</h3><p>{escape(content_goal)}</p></article>'
        )

    def _fallback_css(self, style_scope_id: str, style_guide: InteractiveHtmlCourseStyleGuide) -> str:
        colors = style_guide.color_tokens
        accent = colors.get("primary", "#5c6df6")
        surface = colors.get("surface", "#fffdf8")
        text = colors.get("text", "#243044")
        return (
            f".{style_scope_id} {{ --ih-accent: {accent}; --ih-surface: {surface}; --ih-text: {text}; "
            "max-width: 920px; margin: 0 auto; padding: 24px; overflow-wrap: break-word; }}\n"
            f".{style_scope_id} .ih-block {{ background: var(--ih-surface); border: 1px solid rgba(36,48,68,.12); "
            "border-radius: 20px; padding: 22px; margin-bottom: 18px; }}\n"
        )
