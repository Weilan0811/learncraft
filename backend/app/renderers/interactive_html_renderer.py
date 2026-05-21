from app.schemas.render.interactive_html import (
    InteractiveHtmlRenderBlock,
    InteractiveHtmlRenderModel,
    InteractiveHtmlRenderSection,
)
from app.schemas.specs.interactive_html import InteractiveHtmlSpec


class InteractiveHtmlRenderer:
    """Render InteractiveHtmlSpec into frontend InteractiveHtmlRenderModel."""

    def render(self, spec: InteractiveHtmlSpec, _elements: list) -> InteractiveHtmlRenderModel:
        sections = [self._render_section(sec) for sec in spec.sections]
        return self._assemble(spec, sections)

    def render_unit(self, section, _elements: list) -> InteractiveHtmlRenderSection:
        return self._render_section(section)

    def _render_section(self, section) -> InteractiveHtmlRenderSection:
        blocks: list[InteractiveHtmlRenderBlock] = []
        for block in section.blocks:
            block_dict = block.model_dump(exclude_none=True)
            blocks.append(
                InteractiveHtmlRenderBlock(
                    block_id=block.block_id,
                    type=block.type,
                    title=block.title,
                    block_data=block_dict,
                    metadata={
                        "citations": [c.model_dump() for c in (getattr(block, "citations", None) or [])],
                    },
                )
            )
        return InteractiveHtmlRenderSection(
            section_id=section.section_id,
            title=section.title,
            learning_goal=section.learning_goal,
            render_blocks=blocks,
        )

    def _assemble(self, spec: InteractiveHtmlSpec, sections: list[InteractiveHtmlRenderSection]) -> InteractiveHtmlRenderModel:
        return InteractiveHtmlRenderModel(
            lesson_id=spec.lesson_id,
            title=spec.title,
            subtitle=spec.subtitle,
            meta=spec.meta.model_dump() if spec.meta else {},
            pedagogy=spec.pedagogy.model_dump(),
            sections=sections,
            citations=[c.model_dump() for c in spec.citations],
        )
