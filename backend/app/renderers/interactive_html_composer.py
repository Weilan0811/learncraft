import json
import os
from typing import cast

from app.schemas.render.interactive_html import InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
from app.schemas.specs.interactive_html_style import InteractiveHtmlCourseStyleGuide
from app.services.llm_service import get_llm_service
from app.validators.interactive_html_validator import (
    InteractiveHtmlValidationReport,
    sanitize_rendered_unit,
    validate_rendered_unit,
)


class InteractiveHtmlRenderError(RuntimeError):
    pass


class InteractiveHtmlComposer:
    MAX_REPAIR_ATTEMPTS = 2

    def compose_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        retrieval_context: list | None = None,
        repair_context: dict | None = None,
    ) -> InteractiveHtmlRenderedUnit:
        rendered = self._generate_rendered_unit(section_spec, style_guide, retrieval_context, repair_context)
        rendered = sanitize_rendered_unit(rendered)

        report = validate_rendered_unit(rendered)
        if report.ok:
            return rendered

        for _ in range(self.MAX_REPAIR_ATTEMPTS):
            rendered = self._repair_rendered_unit(rendered, report, section_spec, style_guide)
            rendered = sanitize_rendered_unit(rendered)
            report = validate_rendered_unit(rendered)
            if report.ok:
                return rendered

        raise InteractiveHtmlRenderError(
            "InteractiveHtmlRenderedUnit failed validation after repair: "
            + "; ".join(f"{issue.path}: {issue.message}" for issue in report.issues)
        )

    def _generate_rendered_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        retrieval_context: list | None = None,
        repair_context: dict | None = None,
    ) -> InteractiveHtmlRenderedUnit:
        prompt = self._build_render_prompt(section_spec, style_guide, retrieval_context, repair_context)
        llm_service = get_llm_service()
        return cast(
            InteractiveHtmlRenderedUnit,
            llm_service.generate_structured(prompt=prompt, schema=InteractiveHtmlRenderedUnit),
        )

    def _repair_rendered_unit(
        self,
        rendered_unit: InteractiveHtmlRenderedUnit,
        report: InteractiveHtmlValidationReport,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> InteractiveHtmlRenderedUnit:
        prompt = self._build_repair_prompt(rendered_unit, report, section_spec, style_guide)
        llm_service = get_llm_service()
        return cast(
            InteractiveHtmlRenderedUnit,
            llm_service.generate_structured(prompt=prompt, schema=InteractiveHtmlRenderedUnit),
        )

    def _build_render_prompt(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        retrieval_context: list | None = None,
        repair_context: dict | None = None,
    ) -> str:
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "generator", "interactive_html_unit_render.md"
        )
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        runtime_contract = json.dumps({
            "allowed_data_actions": [
                "complete-section", "tab-select", "flow-next", "flow-prev", "flow-reset",
                "single-choice", "multiple-choice", "short-answer", "sequence-select", "match-select",
            ],
            "required_root_tag": "section",
            "required_root_attrs": ["id", "class", "data-section-id"],
            "required_block_attrs": ["data-block-id", "data-block-type"],
            "required_interaction_attrs": ["data-ih-action", "data-interaction-id"],
        }, ensure_ascii=False, indent=2)

        retrieval_text = ""
        if retrieval_context:
            retrieval_text = json.dumps(
                [chunk.model_dump() if hasattr(chunk, "model_dump") else chunk for chunk in retrieval_context],
                ensure_ascii=False,
                indent=2,
            )

        prompt = template.format(
            unit_spec=section_spec.model_dump_json(indent=2),
            style_guide=style_guide.model_dump_json(indent=2),
            runtime_contract=runtime_contract,
            retrieval_context=retrieval_text or "无",
        )
        if repair_context:
            prompt += (
                "\n\n## Repair context\n"
                "The previous render attempt failed before producing a valid InteractiveHtmlRenderedUnit. "
                "Regenerate the full rendered unit from scratch. Use the errors below as diagnostic input only.\n"
                f"{json.dumps(repair_context, ensure_ascii=False, indent=2)}"
            )
        return prompt

    def _build_repair_prompt(
        self,
        rendered_unit: InteractiveHtmlRenderedUnit,
        report: InteractiveHtmlValidationReport,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> str:
        template_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "reviewer", "interactive_html_render_repair.md"
        )
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        issues_text = json.dumps(
            [{"path": issue.path, "message": issue.message} for issue in report.issues],
            ensure_ascii=False,
            indent=2,
        )

        return template.format(
            rendered_unit=rendered_unit.model_dump_json(indent=2),
            validation_report=issues_text,
            unit_spec=section_spec.model_dump_json(indent=2),
            style_guide=style_guide.model_dump_json(indent=2),
        )

    def _fallback_rendered_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> InteractiveHtmlRenderedUnit:
        scope_id = f"ih-scope-{section_spec.section_id}"
        html = self._build_fallback_html(section_spec, scope_id)
        css = self._build_fallback_css(scope_id, style_guide)
        return InteractiveHtmlRenderedUnit(
            section_id=section_spec.section_id,
            title=section_spec.title,
            learning_goal=section_spec.learning_goal,
            style_scope_id=scope_id,
            html_fragment=html,
            css_fragment=css,
            block_manifest=[],
            interaction_manifest=[],
            render_notes={"fallback": True},
        )

    def fallback_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> InteractiveHtmlRenderedUnit:
        return self._fallback_rendered_unit(section_spec, style_guide)

    def _build_fallback_html(self, spec: InteractiveHtmlSectionSpec, scope_id: str) -> str:
        blocks_html = ""
        for block in spec.teaching_flow:
            blocks_html += (
                f'<div class="ih-block ih-block--{block.block_type}" '
                f'data-block-id="{block.block_id}" data-block-type="{block.block_type}">'
                f"<h3>{block.title}</h3>"
                f"<p>{block.content_goal}</p>"
            )
            for item in block.must_cover:
                blocks_html += f"<p>• {item}</p>"
            blocks_html += "</div>"
        return (
            f'<section id="{spec.section_id}" class="ih-unit {scope_id}" '
            f'data-section-id="{spec.section_id}">'
            f"<h2>{spec.title}</h2>"
            f"<p>{spec.learning_goal}</p>"
            f"{blocks_html}"
            f"</section>"
        )

    def _build_fallback_css(self, scope_id: str, style_guide: InteractiveHtmlCourseStyleGuide) -> str:
        colors = style_guide.color_tokens
        accent = colors.get("primary", "#5b6cff")
        surface = colors.get("surface", "#ffffff")
        text = colors.get("text", "#1f2937")
        return (
            f".{scope_id} {{\n"
            f"  --ih-accent: {accent};\n"
            f"  --ih-surface: {surface};\n"
            f"  --ih-text: {text};\n"
            f"  max-width: 800px;\n"
            f"  margin: 0 auto;\n"
            f"  padding: 24px;\n"
            f"  overflow-wrap: break-word;\n"
            f"  word-break: break-word;\n"
            f"}}\n"
            f".{scope_id} .ih-block {{\n"
            f"  background: var(--ih-surface);\n"
            f"  border-radius: 16px;\n"
            f"  padding: 20px;\n"
            f"  margin-bottom: 16px;\n"
            f"}}\n"
            f".{scope_id} h2 {{\n"
            f"  color: var(--ih-accent);\n"
            f"}}\n"
            f".{scope_id} h3 {{\n"
            f"  color: var(--ih-text);\n"
            f"}}\n"
        )
