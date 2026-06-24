from app.generators.unit_specs import (
    build_interactive_html_unit_spec_fallback,
    build_lecture_unit_spec_fallback,
    build_slide_unit_spec_fallback,
    repair_unit_spec_with_llm,
)
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import current_outline_unit, unit_progress


def repair_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    retry_key = f"unit_spec_repair:{unit.id}"
    retry_counts = dict(state.retry_counts)
    retry_counts[retry_key] = retry_counts.get(retry_key, 0) + 1
    validation_errors = _current_spec_errors(state)

    try:
        repaired_spec = repair_unit_spec_with_llm(
            state,
            unit,
            [chunk.id for chunk in state.current_unit_context] or unit.source_chunk_ids,
            validation_errors,
        )
        return {
            "current_unit_spec": repaired_spec,
            "spec_validation_report": None,
            "errors": _without_current_spec_errors(state),
            "retry_counts": retry_counts,
            "current_node": "repair_unit_spec",
            "progress": unit_progress(state, "repairing_unit_spec", current_node="repair_unit_spec"),
        }
    except Exception as exc:
        return {
            "errors": [*_without_current_spec_errors(state), f"unit_spec repair failed: {exc}"],
            "retry_counts": retry_counts,
            "current_node": "repair_unit_spec",
            "progress": unit_progress(state, "repairing_unit_spec", current_node="repair_unit_spec"),
        }


def fallback_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    chunk_ids = [chunk.id for chunk in state.current_unit_context] or unit.source_chunk_ids
    if state.content_type == "slide_deck":
        fallback_spec = build_slide_unit_spec_fallback(state, unit, chunk_ids)
    elif state.content_type == "interactive_html":
        fallback_spec = build_interactive_html_unit_spec_fallback(state, unit, chunk_ids)
    else:
        fallback_spec = build_lecture_unit_spec_fallback(state, unit, chunk_ids)

    return {
        "current_unit_spec": fallback_spec,
        "spec_validation_report": None,
        "errors": _without_current_spec_errors(state),
        "current_node": "fallback_unit_spec",
        "progress": unit_progress(state, "fallback_unit_spec", current_node="fallback_unit_spec"),
    }


def _current_spec_errors(state: ContentGenerationState) -> list[str]:
    if not state.spec_validation_report:
        return []
    return [str(error) for error in state.spec_validation_report.get("errors", [])]


def _without_current_spec_errors(state: ContentGenerationState) -> list[str]:
    current_errors = set(_current_spec_errors(state))
    return [
        error
        for error in state.errors
        if error not in current_errors and not error.startswith("unit_spec repair failed:")
    ]


__all__ = ["repair_unit_spec", "fallback_unit_spec"]
