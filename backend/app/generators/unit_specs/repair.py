from app.generators.common.unit_prompt_builder import build_unit_spec_repair_prompt
from app.schemas.outline import OutlineUnit
from app.schemas.specs import InteractiveHtmlSectionSpec, LectureSection, SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def repair_unit_spec_with_llm(
    state: ContentGenerationState,
    unit: OutlineUnit,
    chunk_ids: list[str],
    validation_errors: list[str],
) -> LectureSection | SlideSpecPage | InteractiveHtmlSectionSpec:
    schema = _schema_for_content_type(state.content_type)
    unit_spec_id = _unit_spec_id_for_content_type(state.content_type, unit.id)
    prompt = build_unit_spec_repair_prompt(state.content_type, state, unit, unit_spec_id, chunk_ids, validation_errors)
    return get_llm_service().generate_structured(prompt=prompt, schema=schema)


def _schema_for_content_type(content_type: str) -> type[LectureSection] | type[SlideSpecPage] | type[InteractiveHtmlSectionSpec]:
    if content_type == "slide_deck":
        return SlideSpecPage
    if content_type == "interactive_html":
        return InteractiveHtmlSectionSpec
    return LectureSection


def _unit_spec_id_for_content_type(content_type: str, unit_id: str) -> str:
    if content_type == "slide_deck":
        return f"slide_{unit_id}"
    if content_type == "interactive_html":
        return unit_id
    return f"lecture_{unit_id}"
