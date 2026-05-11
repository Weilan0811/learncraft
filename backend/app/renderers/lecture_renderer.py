from app.schemas.elements import ContentElement, ImageElement, MindmapElement
from app.schemas.render import LectureRenderModel, LectureRenderSection, RenderBlock
from app.schemas.specs import ElementReferenceBlock, LectureSpec, TextBlock


class LectureRenderer:
    def render(self, spec: LectureSpec, elements: list[ContentElement]) -> LectureRenderModel:
        sections = [self.render_unit(section, elements) for section in spec.sections]
        return self.assemble(spec, sections)

    def render_unit(self, section, elements: list[ContentElement]) -> LectureRenderSection:
        element_lookup = {element.id: element for element in elements}
        blocks: list[RenderBlock] = []

        for block in section.blocks:
            if isinstance(block, TextBlock):
                blocks.append(
                    RenderBlock(
                        id=block.id,
                        type="text",
                        title=block.title,
                        content=block.content,
                        metadata={"citations": block.citations},
                    )
                )

            elif isinstance(block, ElementReferenceBlock):
                element = element_lookup.get(block.element_id)
                if element:
                    blocks.append(self._element_to_render_block(element))

        return LectureRenderSection(id=section.id, title=section.title, render_blocks=blocks)

    def assemble(self, spec: LectureSpec, sections: list[LectureRenderSection]) -> LectureRenderModel:
        return LectureRenderModel(
            title=spec.title,
            objectives=spec.objectives,
            sections=sections,
            printable_model={
                "title": spec.title,
                "section_count": len(sections),
                "objectives": spec.objectives,
                "sections": [
                    {
                        "id": sec.id,
                        "title": sec.title,
                        "block_count": len(sec.render_blocks)
                    }
                    for sec in sections
                ]
            },
        )
    
    def _element_to_render_block(self, element: ContentElement) -> RenderBlock:
        if isinstance(element, ImageElement):
            return RenderBlock(
                id=element.id,
                type="image",
                title=element.title,
                asset_url=element.asset_url,
                content=element.alt_text,
                metadata={
                    "prompt": element.prompt,
                    "width": element.width,
                    "height": element.height,
                    "format": element.format,
                    **element.metadata
                },
            )
        
        if isinstance(element, MindmapElement):
            return RenderBlock(
                id=element.id,
                type="mindmap",
                title=element.title,
                content=element.markdown,
                metadata={
                    "format": "markmap_markdown",
                    **element.metadata
                },
            )
        
        return RenderBlock(
            id=element.id,
            type=element.type,
            title=element.title,
            content=getattr(element, "content", None) or getattr(element, "markdown", None),
            asset_url=getattr(element, "asset_url", None),
            metadata=element.metadata,
        )
