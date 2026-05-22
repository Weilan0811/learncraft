from html import escape

from app.renderers.interactive_html_explanation_composer import InteractiveHtmlExplanationRender
from app.renderers.interactive_html_interaction_renderer import RenderedInteractionBlock
from app.schemas.render.interactive_html import InteractiveHtmlRenderBlockRef, InteractiveHtmlRenderedUnit
from app.schemas.specs.interactive_html import InteractiveHtmlSectionSpec


INTERACTION_BASE_CSS = """
.{scope} .ih-options {{ display: grid; gap: 12px; margin: 16px 0; }}
.{scope} .ih-option {{ width: 100%; text-align: left; border: 1px solid rgba(36,48,68,.14); background: #fff; color: var(--ih-text, #243044); border-radius: 16px; padding: 13px 15px; cursor: pointer; display: flex; gap: 10px; align-items: flex-start; }}
.{scope} .ih-option::before {{ content: attr(data-option-label); display: inline-grid; place-items: center; flex: 0 0 28px; width: 28px; height: 28px; border-radius: 999px; background: rgba(92,109,246,.12); color: var(--ih-accent, #5c6df6); font-weight: 800; }}
.{scope} .ih-option.is-selected, .{scope} .ih-option.selected, .{scope} .ih-option.active {{ border-color: var(--ih-accent, #5c6df6); background: rgba(92,109,246,.10); }}
.{scope} .ih-option.is-correct {{ border-color: rgba(22,163,74,.55); background: rgba(22,163,74,.08); }}
.{scope} .ih-option.is-wrong {{ border-color: rgba(220,38,38,.46); background: rgba(220,38,38,.06); }}
.{scope} .ih-submit {{ border: 0; border-radius: 999px; padding: 10px 18px; background: var(--ih-accent, #5c6df6); color: #fff; font-weight: 800; cursor: pointer; }}
.{scope} .ih-submit.secondary {{ background: #243044; }}
.{scope} .ih-textarea {{ width: 100%; min-height: 120px; resize: vertical; border: 1px solid rgba(36,48,68,.14); border-radius: 16px; padding: 14px 16px; background: #fff; color: var(--ih-text, #243044); }}
.{scope} .ih-feedback {{ display: none; margin-top: 14px; border-radius: 16px; padding: 14px 16px; background: rgba(255,255,255,.78); border: 1px solid rgba(36,48,68,.12); }}
.{scope} .ih-feedback.is-visible {{ display: block; }}
.{scope} .ih-feedback.success {{ border-color: rgba(22,163,74,.35); background: rgba(22,163,74,.08); }}
.{scope} .ih-feedback.warn {{ border-color: rgba(255,184,107,.55); background: rgba(255,184,107,.12); }}
.{scope} .scenario-box {{ display: grid; grid-template-columns: minmax(0,.9fr) minmax(0,1.1fr); gap: 16px; }}
.{scope} .scenario-card {{ border-radius: 18px; padding: 18px; background: #243044; color: #fff; }}
.{scope} .scenario-card .tag {{ display: inline-block; background: rgba(255,255,255,.14); border-radius: 999px; padding: 4px 10px; font-size: 12px; margin-bottom: 10px; }}
@media (max-width: 760px) {{ .{scope} .scenario-box {{ grid-template-columns: 1fr; }} }}
"""


class UnitHtmlAssembler:
    def assemble(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        explanation_render: InteractiveHtmlExplanationRender,
        interaction_blocks: dict[str, RenderedInteractionBlock],
        style_scope_id: str,
    ) -> InteractiveHtmlRenderedUnit:
        html_parts: list[str] = []
        block_manifest: list[InteractiveHtmlRenderBlockRef] = []
        interaction_manifest = []
        warnings: list[str] = []

        for block in section_spec.teaching_flow:
            interaction_block = interaction_blocks.get(block.block_id)
            if interaction_block:
                html_parts.append(interaction_block.html_fragment)
                block_manifest.append(interaction_block.block_manifest_item)
                interaction_manifest.append(interaction_block.interaction_manifest_item)
                continue

            explanation_html = explanation_render.block_html_map.get(block.block_id)
            if explanation_html:
                html_parts.append(explanation_html)
            else:
                warnings.append(block.block_id)
                html_parts.append(self._missing_block(block.block_id, block.block_type))

            block_manifest.append(InteractiveHtmlRenderBlockRef(
                block_id=block.block_id,
                type=block.block_type,
                title=block.title,
                teaching_role=block.teaching_role,
                interaction_ids=[],
            ))

        css = "\n\n".join([
            explanation_render.css_fragment.strip(),
            INTERACTION_BASE_CSS.format(scope=style_scope_id).strip(),
        ]).strip()
        html_fragment = (
            f'<section id="{escape(section_spec.section_id)}" class="ih-unit {escape(style_scope_id)}" '
            f'data-section-id="{escape(section_spec.section_id)}">\n'
            + "\n".join(html_parts)
            + "\n</section>"
        )

        return InteractiveHtmlRenderedUnit(
            section_id=section_spec.section_id,
            title=section_spec.title,
            learning_goal=section_spec.learning_goal,
            style_scope_id=style_scope_id,
            html_fragment=html_fragment,
            css_fragment=css,
            block_manifest=block_manifest,
            interaction_manifest=interaction_manifest,
            render_notes={
                **explanation_render.render_notes,
                "missing_blocks": warnings,
                "interaction_template_renderer": "p0_four_type",
            },
        )

    def _missing_block(self, block_id: str, block_type: str) -> str:
        return (
            f'<article class="ih-block ih-warning" data-block-id="{escape(block_id)}" '
            f'data-block-type="{escape(block_type)}">'
            "<h3>本段内容需要补充</h3>"
            "<p>系统未能成功生成该教学块，已记录用于修复。</p>"
            "</article>"
        )
