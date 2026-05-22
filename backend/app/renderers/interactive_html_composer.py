import json
import os

from app.renderers.interactive_html_explanation_composer import ExplanationHtmlComposer
from app.renderers.interactive_html_explanation_composer import InteractiveHtmlExplanationRender
from app.renderers.interactive_html_explanation_composer import INTERACTION_BLOCK_TYPES
from app.renderers.interactive_html_interaction_renderer import InteractionTemplateRenderer
from app.renderers.interactive_html_unit_assembler import UnitHtmlAssembler
from app.schemas.render.interactive_html import InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec
from app.schemas.specs.interactive_html_style import InteractiveHtmlCourseStyleGuide
from app.validators.interactive_html_validator import (
    sanitize_rendered_unit,
    validate_rendered_unit,
)


class InteractiveHtmlRenderError(RuntimeError):
    pass


class InteractiveHtmlComposer:
    def __init__(
        self,
        explanation_composer: ExplanationHtmlComposer | None = None,
        interaction_renderer: InteractionTemplateRenderer | None = None,
        unit_assembler: UnitHtmlAssembler | None = None,
    ) -> None:
        self.explanation_composer = explanation_composer or ExplanationHtmlComposer()
        self.interaction_renderer = interaction_renderer or InteractionTemplateRenderer()
        self.unit_assembler = unit_assembler or UnitHtmlAssembler()

    def compose_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        retrieval_context: list | None = None,
        repair_context: dict | None = None,
    ) -> InteractiveHtmlRenderedUnit:
        style_scope_id = f"ih-scope-{section_spec.section_id}"
        interaction_blocks = self.interaction_renderer.render(section_spec, style_scope_id)
        try:
            explanation_render = self.explanation_composer.compose(
                section_spec=section_spec,
                style_guide=style_guide,
                style_scope_id=style_scope_id,
                retrieval_context=retrieval_context,
            )
        except Exception as exc:
            explanation_render = self._fallback_explanation_render(section_spec, style_guide, style_scope_id, exc)
        rendered = self.unit_assembler.assemble(
            section_spec=section_spec,
            explanation_render=explanation_render,
            interaction_blocks=interaction_blocks,
            style_scope_id=style_scope_id,
        )
        rendered = sanitize_rendered_unit(rendered)
        report = validate_rendered_unit(rendered)
        if report.ok:
            return rendered
        raise InteractiveHtmlRenderError(
            "InteractiveHtmlRenderedUnit failed validation: "
            + "; ".join(f"{issue.path}: {issue.message}" for issue in report.issues)
        )

    def _build_render_prompt(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        retrieval_context: list | None = None,
        repair_context: dict | None = None,
    ) -> str:
        style_scope_id = f"ih-scope-{section_spec.section_id}"
        return self.explanation_composer._build_render_prompt(
            section_spec=section_spec,
            style_guide=style_guide,
            style_scope_id=style_scope_id,
            retrieval_context=retrieval_context,
        )

    def _fallback_explanation_render(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
        style_scope_id: str,
        exc: Exception | None = None,
    ) -> InteractiveHtmlExplanationRender:
        interaction_block_ids = {spec.block_id for spec in section_spec.interaction_specs}
        fallback_composer = ExplanationHtmlComposer()
        render_notes: dict[str, object] = {"fallback": True}
        if exc is not None:
            render_notes["explanation_error"] = str(exc)
        return InteractiveHtmlExplanationRender(
            section_id=section_spec.section_id,
            style_scope_id=style_scope_id,
            block_html_map={
                block.block_id: fallback_composer._fallback_block(
                    block.block_id,
                    block.title,
                    block.content_goal,
                )
                for block in section_spec.teaching_flow
                if block.block_type not in INTERACTION_BLOCK_TYPES and block.block_id not in interaction_block_ids
            },
            css_fragment=fallback_composer._fallback_css(style_scope_id, style_guide),
            render_notes=render_notes,
        )

    def _build_repair_prompt(
        self,
        rendered_unit: InteractiveHtmlRenderedUnit,
        report,
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

    def fallback_unit(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_guide: InteractiveHtmlCourseStyleGuide,
    ) -> InteractiveHtmlRenderedUnit:
        style_scope_id = f"ih-scope-{section_spec.section_id}"
        explanation_render = self._fallback_explanation_render(section_spec, style_guide, style_scope_id)
        interaction_blocks = self.interaction_renderer.render(section_spec, style_scope_id)
        return self.unit_assembler.assemble(section_spec, explanation_render, interaction_blocks, style_scope_id)
