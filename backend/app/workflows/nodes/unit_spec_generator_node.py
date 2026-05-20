from app.content_types.registry import get_content_type_profile
from app.generators.unit_spec_generators import (
    build_interactive_html_unit_spec,
    build_lecture_unit_spec,
    build_slide_unit_spec,
)
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import current_outline_unit, unit_progress


def generate_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    chunk_ids = [chunk.id for chunk in state.current_unit_context] or unit.source_chunk_ids
    profile = get_content_type_profile(state.content_type)
    if profile.generator_name == "slide_unit_spec":
        unit_spec = build_slide_unit_spec(state, unit, chunk_ids)
    elif profile.generator_name == "interactive_html":
        unit_spec = build_interactive_html_unit_spec(state, unit, chunk_ids)
    else:
        unit_spec = build_lecture_unit_spec(state, unit, chunk_ids)
    return {
        "current_unit_spec": unit_spec,
        "current_node": "generate_unit_spec",
        "progress": unit_progress(state, "generating_unit", current_node="generate_unit_spec"),
    }


__all__ = ["generate_unit_spec"]
