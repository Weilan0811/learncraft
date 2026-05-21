from app.renderers.interactive_html_composer import InteractiveHtmlComposer
from app.schemas.specs import InteractiveHtmlSectionSpec
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.unit_renderer_node import (
    build_render_unit_update,
    get_or_build_style_guide,
    render_error_messages,
)


def repair_render_unit(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
        return {
            "errors": [*state.errors, "render_unit repair is only supported for interactive_html"],
            "current_node": "repair_render_unit",
        }
    unit_id = state.current_unit_id or state.current_unit_spec.section_id
    retry_key = f"render_unit_repair:{unit_id}"
    retry_counts = dict(state.retry_counts)
    retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1

    try:
        rendered = InteractiveHtmlComposer().compose_unit(
            section_spec=state.current_unit_spec,
            style_guide=get_or_build_style_guide(state),
            retrieval_context=state.current_unit_context or None,
            repair_context={"errors": render_error_messages(state)},
        )
        update = build_render_unit_update(
            state,
            unit_id,
            rendered.model_dump(mode="json"),
            current_node="repair_render_unit",
            stage="repairing_render_unit",
        )
        update["retry_counts"] = retry_counts
        return update
    except Exception as exc:
        return {
            "errors": [*state.errors, f"render_unit failed: {exc}"],
            "retry_counts": retry_counts,
            "current_node": "repair_render_unit",
        }


def fallback_render_unit(state: ContentGenerationState) -> dict[str, object]:
    if not isinstance(state.current_unit_spec, InteractiveHtmlSectionSpec):
        return {
            "errors": [*state.errors, "render_unit fallback is only supported for interactive_html"],
            "current_node": "fallback_render_unit",
        }
    unit_id = state.current_unit_id or state.current_unit_spec.section_id
    rendered = InteractiveHtmlComposer().fallback_unit(
        section_spec=state.current_unit_spec,
        style_guide=get_or_build_style_guide(state),
    )
    return build_render_unit_update(
        state,
        unit_id,
        rendered.model_dump(mode="json"),
        current_node="fallback_render_unit",
        stage="fallback_render_unit",
    )


__all__ = ["repair_render_unit", "fallback_render_unit"]
