from datetime import UTC, datetime

from app.renderers.interactive_html_composer import InteractiveHtmlComposer
from app.renderers.interactive_html_renderer import InteractiveHtmlRenderer
from app.renderers.lecture_renderer import LectureRenderer
from app.renderers.slide_renderer import SlideRenderer
from app.schemas.render import (
    InteractiveHtmlRenderModel,
    InteractiveHtmlRenderedUnit,
    LectureRenderModel,
    LectureRenderSection,
    SlidePageModel,
    SlideRenderModel,
)
from app.schemas.specs import InteractiveHtmlSectionSpec, InteractiveHtmlSpec, LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.specs.interactive_html import InteractiveHtmlMeta
from app.schemas.specs.interactive_html_style import DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE, InteractiveHtmlCourseStyleGuide
from app.schemas.state import ContentGenerationState, RenderUnitSnapshot
from app.workflows.nodes.helpers import unit_progress


MAX_RENDER_TRANSPORT_RETRIES = 1


def render_unit(state: ContentGenerationState) -> dict[str, object]:
    if state.current_unit_spec is None:
        return {"errors": state.errors + ["current_unit_spec is required for unit rendering"], "current_node": "render_unit"}
    unit_id = state.current_unit_id or state.current_unit_spec.id
    unit_elements = _current_unit_elements(state)

    try:
        if isinstance(state.current_unit_spec, LectureSection):
            fragment = LectureRenderer().render_unit(state.current_unit_spec, unit_elements).model_dump(mode="json")
        elif isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
            style_guide = get_or_build_style_guide(state)
            rendered_unit = InteractiveHtmlComposer().compose_unit(
                section_spec=state.current_unit_spec,
                style_guide=style_guide,
                retrieval_context=state.current_unit_context or None,
            )
            fragment = rendered_unit.model_dump(mode="json")
        elif isinstance(state.current_unit_spec, SlideSpecPage):
            deck_spec = _partial_slide_deck_spec(state, [state.current_unit_spec])
            fragment = SlideRenderer().render_unit(state.current_unit_spec, unit_elements, deck_spec).model_dump(mode="json")
        else:
            return {"errors": state.errors + [f"Unsupported unit spec for rendering: {type(state.current_unit_spec).__name__}"], "current_node": "render_unit"}
    except Exception as exc:
        update: dict[str, object] = {
            "errors": [*state.errors, f"render_unit failed: {exc}"],
            "current_node": "render_unit",
            "progress": unit_progress(state, "rendering_unit", current_node="render_unit"),
        }
        if _is_render_transport_error(exc):
            retry_counts = dict(state.retry_counts)
            retry_key = f"render_unit_transport:{unit_id}"
            retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1
            update["retry_counts"] = retry_counts
        return update

    return build_render_unit_update(state, unit_id, fragment, current_node="render_unit", stage="rendering_unit")


def build_render_unit_update(
    state: ContentGenerationState,
    unit_id: str,
    fragment: dict[str, object],
    current_node: str,
    stage: str,
) -> dict[str, object]:
    render_units = dict(state.render_units)

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
        "errors": _without_render_errors(state),
        "current_node": current_node,
        "progress": unit_progress(state, stage, current_node=current_node),
    }


def route_after_render_unit(state: ContentGenerationState) -> str:
    unit_id = state.current_unit_id or ""
    snapshot = state.render_units.get(unit_id)
    if snapshot and snapshot.status == "rendered":
        return "pass"
    if isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
        transport_retry_key = f"render_unit_transport:{unit_id}"
        if _last_render_error_is_transport(state):
            if state.retry_counts.get(transport_retry_key, 0) <= MAX_RENDER_TRANSPORT_RETRIES:
                return "retry"
            if bool((state.normalized_request or {}).get("allow_fallback", False)):
                return "fallback"
            return "fail"
        retry_key = f"render_unit_repair:{unit_id}"
        if state.retry_counts.get(retry_key, 0) < 1:
            return "repair"
        if bool((state.normalized_request or {}).get("allow_fallback", False)):
            return "fallback"
    return "fail"


def get_or_build_style_guide(state: ContentGenerationState) -> InteractiveHtmlCourseStyleGuide:
    if state.style_guide:
        return InteractiveHtmlCourseStyleGuide.model_validate(state.style_guide)
    return DEFAULT_INTERACTIVE_HTML_STYLE_GUIDE


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
        rendered_units = [
            InteractiveHtmlRenderedUnit.model_validate(snapshot.render_fragment)
            for snapshot in ordered
            if snapshot.status == "rendered"
        ]
        style_guide = get_or_build_style_guide(state)
        return InteractiveHtmlRenderer().assemble(
            lesson_id=f"lesson_{state.request_id}",
            title=state.outline.title if state.outline else state.topic,
            rendered_units=rendered_units,
            style_guide=style_guide,
        )
    sections = [LectureRenderSection.model_validate(snapshot.render_fragment) for snapshot in ordered if snapshot.status == "rendered"]
    spec = LectureSpec(
        id=f"partial_lecture_{state.request_id}",
        title=state.outline.title if state.outline else state.topic,
        objectives=state.outline.learning_objectives if state.outline else [],
        sections=[],
    )
    return LectureRenderer().assemble(spec, sections)


def render_error_messages(state: ContentGenerationState) -> list[str]:
    return [error for error in state.errors if error.startswith("render_unit failed:")]


def _last_render_error_is_transport(state: ContentGenerationState) -> bool:
    errors = render_error_messages(state)
    return bool(errors) and _is_render_transport_error_message(errors[-1])


def _is_render_transport_error(exc: Exception) -> bool:
    return _is_render_transport_error_message(str(exc))


def _is_render_transport_error_message(message: str) -> bool:
    transport_markers = (
        "ReadTimeout",
        "ConnectTimeout",
        "PoolTimeout",
        "WriteTimeout",
        "TimeoutException",
        "ConnectError",
        "RemoteProtocolError",
        "LLM request failed after retries",
    )
    return any(marker in message for marker in transport_markers)


def _without_render_errors(state: ContentGenerationState) -> list[str]:
    return [error for error in state.errors if not error.startswith("render_unit failed:")]


__all__ = [
    "render_unit",
    "route_after_render_unit",
    "build_render_unit_update",
    "get_or_build_style_guide",
    "render_error_messages",
]
