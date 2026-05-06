from app.schemas.elements import ContentElement
from app.schemas.render import LectureRenderModel, LectureRenderSection, RenderBlock
from app.schemas.specs import LectureSpec, TextBlock


class LectureRenderer:
    def render(self, spec: LectureSpec, elements: list[ContentElement]) -> LectureRenderModel:
        element_lookup = {element.id: element for element in elements}
        sections: list[LectureRenderSection] = []
        for section in spec.sections:
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
                elif block.element_id in element_lookup:
                    element = element_lookup[block.element_id]
                    blocks.append(
                        RenderBlock(
                            id=element.id,
                            type=element.type,
                            title=element.title,
                            asset_url=getattr(element, "asset_url", None),
                            content=getattr(element, "content", None) or getattr(element, "markdown", None),
                            metadata=element.metadata,
                        )
                    )
            sections.append(LectureRenderSection(id=section.id, title=section.title, render_blocks=blocks))

        return LectureRenderModel(
            title=spec.title,
            objectives=spec.objectives,
            sections=sections,
            printable_model={"title": spec.title, "section_count": len(sections), "stub": True},
        )
