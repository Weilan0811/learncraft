from datetime import UTC, datetime

from app.renderers.interactive_html_renderer import InteractiveHtmlRenderer
from app.renderers.lecture_renderer import LectureRenderer
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.render import (
    InteractiveHtmlRenderModel,
    InteractiveHtmlRenderSection,
    LectureRenderModel,
    LectureRenderSection,
    SlidePageModel,
    SlideRenderModel,
)
from app.schemas.specs import InteractiveHtmlSectionSpec, InteractiveHtmlSpec, LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.specs.interactive_html import InteractiveHtmlMeta
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot
from app.workflows.nodes.helpers import unit_progress


def render_unit(state: ContentGenerationState) -> dict[str, object]:
    if state.current_unit_spec is None:
        return {"errors": state.errors + ["current_unit_spec is required for unit rendering"], "current_node": "render_unit"}
    unit_id = state.current_unit_id or state.current_unit_spec.id
    unit_elements = _current_unit_elements(state)
    render_units = dict(state.render_units)

    if isinstance(state.current_unit_spec, LectureSection):
        fragment = LectureRenderer().render_unit(state.current_unit_spec, unit_elements).model_dump(mode="json")
    elif isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
        fragment = InteractiveHtmlRenderer().render_unit(state.current_unit_spec, unit_elements).model_dump(mode="json")
    elif isinstance(state.current_unit_spec, SlideSpecPage):
        deck_spec = _partial_slide_deck_spec(state, [state.current_unit_spec])
        fragment = SlideRenderer().render_unit(state.current_unit_spec, unit_elements, deck_spec).model_dump(mode="json")
    else:
        return {"errors": state.errors + [f"Unsupported unit spec for rendering: {type(state.current_unit_spec).__name__}"], "current_node": "render_unit"}

    render_units[unit_id] = RenderUnitSnapshot(
        unit_id=unit_id,
        order=int(getattr(state.current_unit_spec, "order", None) or len(render_units) + 1),
        content_type=state.content_type,
        status="rendered",
        render_fragment=fragment,
        updated_at=datetime.now(UTC).isoformat(),
    )
    return {
        "render_units": render_units,
        "partial_render_model": _build_partial_render_model(state, render_units),
        "current_node": "render_unit",
        "progress": unit_progress(state, "rendering_unit", current_node="render_unit"),
    }


def _current_unit_elements(state: ContentGenerationState):
    current_ids = {request.element_id for request in state.current_unit_element_requests}
    return [element for element in state.elements if element.id in current_ids]


def _partial_slide_deck_spec(state: ContentGenerationState, slides: list[SlideSpecPage]) -> SlideDeckSpec:
    return SlideDeckSpec(
        id=f"partial_deck_{state.request_id}",
        title=state.outline.title if state.outline else state.topic,
        metadata={"language": (state.normalized_request or {}).get("language", "zh-CN")},
        slides=slides,
    )


def _build_partial_render_model(state: ContentGenerationState, render_units: dict[str, RenderUnitSnapshot]):
    ordered = sorted(render_units.values(), key=lambda snapshot: snapshot.order)
    if state.content_type == "slide_deck":
        pages = [SlidePageModel.model_validate(snapshot.render_fragment) for snapshot in ordered if snapshot.status == "rendered"]
        return SlideRenderModel(title=state.outline.title if state.outline else state.topic, pages=pages)
    if state.content_type == "interactive_html":
        sections = [InteractiveHtmlRenderSection.model_validate(snapshot.render_fragment) for snapshot in ordered if snapshot.status == "rendered"]
        spec = InteractiveHtmlSpec(
            lesson_id=f"partial_lesson_{state.request_id}",
            title=state.outline.title if state.outline else state.topic,
            meta=InteractiveHtmlMeta(
                language=(state.normalized_request or {}).get("language", "zh-CN"),
                audience="general",
                difficulty="introductory",
            ),
            sections=[],
        )
        return InteractiveHtmlRenderer()._assemble(spec, sections)
    sections = [LectureRenderSection.model_validate(snapshot.render_fragment) for snapshot in ordered if snapshot.status == "rendered"]
    spec = LectureSpec(
        id=f"partial_lecture_{state.request_id}",
        title=state.outline.title if state.outline else state.topic,
        objectives=state.outline.learning_objectives if state.outline else [],
        sections=[],
    )
    return LectureRenderer().assemble(spec, sections)


__all__ = ["render_unit"]
