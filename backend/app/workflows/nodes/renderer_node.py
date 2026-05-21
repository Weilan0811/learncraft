from app.content_types.registry import get_content_type_profile
from app.renderers.interactive_html_renderer import InteractiveHtmlRenderer
from app.schemas.render.interactive_html import InteractiveHtmlRenderedUnit
from app.schemas.specs import InteractiveHtmlSpec, LectureSpec, SlideDeckSpec
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress
from app.workflows.nodes.unit_renderer_node import get_or_build_style_guide


def route_renderer(state: ContentGenerationState) -> dict[str, object]:
    return {"current_node": "route_renderer"}


def route_renderer_choice(state: ContentGenerationState) -> str:
    return get_content_type_profile(state.content_type).content_type


def lecture_renderer(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.content_spec, LectureSpec):
        return {"errors": state.errors + ["LectureSpec is required for lecture rendering"], "current_node": "lecture_renderer"}
    render_model = get_renderer("lecture").render(state.content_spec, state.elements)
    return {
        "render_model": render_model,
        "current_node": "lecture_renderer",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="rendering", current_node="lecture_renderer")),
    }


def slide_renderer(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.content_spec, SlideDeckSpec):
        return {"errors": state.errors + ["SlideDeckSpec is required for slide rendering"], "current_node": "slide_renderer"}
    render_model = get_renderer("slide_deck").render(state.content_spec, state.elements)
    return {
        "render_model": render_model,
        "current_node": "slide_renderer",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="rendering", current_node="slide_renderer")),
    }


def interactive_html_renderer(state: ContentGenerationState) -> dict[str, object]:
    rendered_units = sorted(
        [snapshot for snapshot in state.render_units.values() if snapshot.status == "rendered"],
        key=lambda snapshot: snapshot.order,
    )
    units = [InteractiveHtmlRenderedUnit.model_validate(snapshot.render_fragment) for snapshot in rendered_units]
    style_guide = get_or_build_style_guide(state)
    render_model = InteractiveHtmlRenderer().assemble(
        lesson_id=f"lesson_{state.request_id}",
        title=state.outline.title if state.outline else state.topic,
        rendered_units=units,
        style_guide=style_guide,
    )
    return {
        "render_model": render_model,
        "current_node": "interactive_html_renderer",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="rendering", current_node="interactive_html_renderer")),
    }


def get_renderer(content_type: str):
    from app.content_types.registry import get_content_type_profile
    return get_content_type_profile(content_type).renderer_factory()


__all__ = ["route_renderer", "route_renderer_choice", "lecture_renderer", "slide_renderer", "interactive_html_renderer", "get_renderer"]
