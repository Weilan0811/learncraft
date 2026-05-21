from app.schemas.render.interactive_html import (
    InteractionRenderRef,
    InteractiveHtmlRenderBlockRef,
    InteractiveHtmlRenderModel,
    InteractiveHtmlRenderedUnit,
    InteractiveRuntimeConfig,
    NavigationItem,
)
from app.schemas.specs.interactive_html import InteractiveHtmlSpec
from app.schemas.specs.interactive_html_style import InteractiveHtmlCourseStyleGuide


class InteractiveHtmlRenderer:
    """Assemble InteractiveHtmlRenderedUnit list into final InteractiveHtmlRenderModel."""

    def assemble(
        self,
        lesson_id: str,
        title: str,
        rendered_units: list[InteractiveHtmlRenderedUnit],
        style_guide: InteractiveHtmlCourseStyleGuide,
        subtitle: str | None = None,
        meta: dict | None = None,
        pedagogy: dict | None = None,
        citations: list[dict] | None = None,
    ) -> InteractiveHtmlRenderModel:
        return InteractiveHtmlRenderModel(
            lesson_id=lesson_id,
            title=title,
            subtitle=subtitle,
            theme=self._theme_from_style(style_guide),
            navigation=[
                NavigationItem(section_id=unit.section_id, title=unit.title, anchor=f"#{unit.section_id}")
                for unit in rendered_units
            ],
            interactions=self._collect_interactions(rendered_units),
            runtime=InteractiveRuntimeConfig(),
            meta=meta or {},
            pedagogy=pedagogy or {},
            sections=rendered_units,
            style_guide=style_guide.model_dump(),
            citations=citations or [],
        )

    def _collect_interactions(self, rendered_units: list[InteractiveHtmlRenderedUnit]) -> list[InteractionRenderRef]:
        refs: list[InteractionRenderRef] = []
        for unit in rendered_units:
            refs.extend(unit.interaction_manifest)
        return refs

    def _theme_from_style(self, style_guide: InteractiveHtmlCourseStyleGuide) -> dict:
        return {
            "style_id": style_guide.style_id,
            "layout_mode": style_guide.layout_mode,
            "visual_keywords": style_guide.visual_keywords,
            "color_tokens": style_guide.color_tokens,
            "spacing_density": style_guide.spacing_density,
        }
