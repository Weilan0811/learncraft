from app.content_types.registry import get_content_type_profile
from app.schemas.specs import LectureSpec, SlideDeckSpec
from app.schemas.state import ContentGenerationState
from app.workflows.routers import get_renderer
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


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


__all__ = ["route_renderer", "route_renderer_choice", "lecture_renderer", "slide_renderer"]
