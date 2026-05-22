from html import escape

from app.schemas.base import SchemaModel
from app.schemas.render.interactive_html import InteractionRenderRef, InteractiveHtmlRenderBlockRef
from app.schemas.specs.interactive_html import (
    InteractiveHtmlInteractionOption,
    InteractiveHtmlInteractionSpec,
    InteractiveHtmlSectionSpec,
    InteractiveHtmlTeachingBlock,
)


class RenderedInteractionBlock(SchemaModel):
    block_id: str
    interaction_id: str
    interaction_type: str
    html_fragment: str
    block_manifest_item: InteractiveHtmlRenderBlockRef
    interaction_manifest_item: InteractionRenderRef


class InteractionTemplateRenderer:
    def render(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        style_scope_id: str,
    ) -> dict[str, RenderedInteractionBlock]:
        blocks_by_id = {block.block_id: block for block in section_spec.teaching_flow}
        rendered: dict[str, RenderedInteractionBlock] = {}
        for spec in section_spec.interaction_specs:
            block = blocks_by_id.get(spec.block_id)
            if spec.type == "single_choice":
                rendered[spec.block_id] = self._render_single_choice(section_spec, spec, block)
            elif spec.type == "multiple_choice":
                rendered[spec.block_id] = self._render_multiple_choice(section_spec, spec, block)
            elif spec.type == "short_answer":
                rendered[spec.block_id] = self._render_short_answer(section_spec, spec, block)
            elif spec.type == "scenario_discussion":
                rendered[spec.block_id] = self._render_scenario_discussion(section_spec, spec, block)
        return rendered

    def _render_single_choice(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        spec: InteractiveHtmlInteractionSpec,
        block: InteractiveHtmlTeachingBlock | None,
    ) -> RenderedInteractionBlock:
        options = "\n".join(
            self._option_button(option, spec, "single-choice", index)
            for index, option in enumerate(spec.options)
        )
        html = f"""
<article class="{self._article_class(spec, 'ih-quiz ih-quiz--single')}" data-block-id="{escape(spec.block_id)}" data-block-type="single_choice">
  {self._header(block, "单选题")}
  <p class="ih-question">{escape(spec.prompt or block.content_goal if block else spec.prompt or "")}</p>
  <div class="ih-options" role="group" aria-label="单选题选项">
    {options}
  </div>
  <div class="ih-feedback" data-ih-feedback-for="{escape(spec.interaction_id)}" aria-live="polite"></div>
</article>
""".strip()
        return self._block(section_spec, spec, block, html)

    def _render_multiple_choice(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        spec: InteractiveHtmlInteractionSpec,
        block: InteractiveHtmlTeachingBlock | None,
    ) -> RenderedInteractionBlock:
        options = "\n".join(
            self._option_button(option, spec, "multiple-choice-toggle", index)
            for index, option in enumerate(spec.options)
        )
        html = f"""
<article class="{self._article_class(spec, 'ih-quiz ih-quiz--multiple')}" data-block-id="{escape(spec.block_id)}" data-block-type="multiple_choice">
  {self._header(block, "多选题")}
  <p class="ih-question">{escape(spec.prompt or block.content_goal if block else spec.prompt or "")}</p>
  <div class="ih-options" role="group" aria-label="多选题选项">
    {options}
  </div>
  <button type="button" class="ih-submit" data-ih-action="multiple-choice-submit" data-interaction-id="{escape(spec.interaction_id)}">提交答案</button>
  <div class="ih-feedback" data-ih-feedback-for="{escape(spec.interaction_id)}" aria-live="polite"></div>
</article>
""".strip()
        return self._block(section_spec, spec, block, html)

    def _render_short_answer(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        spec: InteractiveHtmlInteractionSpec,
        block: InteractiveHtmlTeachingBlock | None,
    ) -> RenderedInteractionBlock:
        html = f"""
<article class="{self._article_class(spec, 'ih-short-answer')}" data-block-id="{escape(spec.block_id)}" data-block-type="short_answer">
  {self._header(block, "简答题")}
  <p class="ih-question">{escape(spec.prompt or block.content_goal if block else spec.prompt or "")}</p>
  <textarea class="ih-textarea" data-ih-input-for="{escape(spec.interaction_id)}" placeholder="{escape(spec.placeholder or '请输入你的回答')}"></textarea>
  <div class="ih-actions">
    <button type="button" class="ih-submit" data-ih-action="short-answer-submit" data-interaction-id="{escape(spec.interaction_id)}" data-min-length="{spec.min_length or 0}" data-reference-points="{escape(_join_reference_points(spec.reference_points))}">提交简答</button>
  </div>
  <div class="ih-feedback" data-ih-feedback-for="{escape(spec.interaction_id)}" aria-live="polite"></div>
</article>
""".strip()
        return self._block(section_spec, spec, block, html)

    def _render_scenario_discussion(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        spec: InteractiveHtmlInteractionSpec,
        block: InteractiveHtmlTeachingBlock | None,
    ) -> RenderedInteractionBlock:
        background = str(spec.scenario.get("background") or "")
        task = str(spec.scenario.get("task") or "")
        html = f"""
<article class="{self._article_class(spec, 'ih-scenario')}" data-block-id="{escape(spec.block_id)}" data-block-type="scenario_discussion">
  {self._header(block, "情景讨论")}
  <div class="scenario-box">
    <div class="scenario-card">
      <div class="tag">场景任务</div>
      <p>{escape(background)}</p>
      <p>{escape(task)}</p>
    </div>
    <div class="scenario-response">
      <p class="ih-question">{escape(spec.prompt or block.content_goal if block else spec.prompt or "")}</p>
      <textarea class="ih-textarea" data-ih-input-for="{escape(spec.interaction_id)}" placeholder="{escape(spec.placeholder or '写下你的判断和理由')}"></textarea>
      <div class="ih-actions">
        <button type="button" class="ih-submit secondary" data-ih-action="scenario-discussion-submit" data-interaction-id="{escape(spec.interaction_id)}" data-min-length="{spec.min_length or 0}" data-reference-points="{escape(_join_reference_points(spec.reference_points))}">提交讨论</button>
      </div>
      <div class="ih-feedback" data-ih-feedback-for="{escape(spec.interaction_id)}" aria-live="polite"></div>
    </div>
  </div>
</article>
""".strip()
        return self._block(section_spec, spec, block, html)

    def _block(
        self,
        section_spec: InteractiveHtmlSectionSpec,
        spec: InteractiveHtmlInteractionSpec,
        block: InteractiveHtmlTeachingBlock | None,
        html: str,
    ) -> RenderedInteractionBlock:
        return RenderedInteractionBlock(
            block_id=spec.block_id,
            interaction_id=spec.interaction_id,
            interaction_type=spec.type,
            html_fragment=html,
            block_manifest_item=InteractiveHtmlRenderBlockRef(
                block_id=spec.block_id,
                type=spec.type,
                title=block.title if block else spec.prompt or spec.type,
                teaching_role=block.teaching_role if block else "diagnose_understanding",
                interaction_ids=[spec.interaction_id],
            ),
            interaction_manifest_item=InteractionRenderRef(
                interaction_id=spec.interaction_id,
                section_id=section_spec.section_id,
                type=spec.type,
                target_concepts=spec.target_concepts,
                event_type=spec.event_type,
            ),
        )

    def _option_button(
        self,
        option: InteractiveHtmlInteractionOption,
        spec: InteractiveHtmlInteractionSpec,
        action: str,
        index: int,
    ) -> str:
        return (
            f'<button type="button" class="ih-option" data-option-label="{_option_label(index)}" '
            f'data-ih-action="{action}" data-interaction-id="{escape(spec.interaction_id)}" '
            f'data-option-id="{escape(option.id)}" data-correct="{str(bool(option.is_correct)).lower()}" '
            f'data-feedback="{escape(option.feedback or "")}">{escape(option.text)}</button>'
        )

    def _article_class(self, spec: InteractiveHtmlInteractionSpec, base: str) -> str:
        variant = f" ih-variant-{spec.visual_variant}" if spec.visual_variant else ""
        return f"ih-block ih-interaction {base}{variant}"

    def _header(self, block: InteractiveHtmlTeachingBlock | None, fallback: str) -> str:
        title = block.title if block else fallback
        return (
            '<div class="ih-block-header"><div>'
            f'<div class="ih-block-kicker">{escape(fallback)}</div>'
            f"<h3>{escape(title)}</h3>"
            "</div></div>"
        )


def _option_label(index: int) -> str:
    return chr(ord("A") + index)


def _join_reference_points(points: list[str]) -> str:
    return "|".join(point.replace("|", " ") for point in points)
