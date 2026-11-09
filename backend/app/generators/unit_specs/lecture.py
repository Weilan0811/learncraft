from typing import cast

from app.core.config import get_settings
from app.core.fallback import allow_generation_fallback
from app.generators.common.unit_prompt_builder import build_unit_spec_prompt
from app.generators.unit_specs.fallback_lecture import build_lecture_unit_spec_fallback
from app.generators.unit_specs.lecture_policy import enforce_single_lecture_image
from app.schemas.outline import OutlineUnit
from app.schemas.specs import LectureSection
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def build_lecture_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> LectureSection:
    settings = get_settings()
    if settings.provider_mode == "stub":
        section = build_lecture_unit_spec_fallback(state, unit, chunk_ids)
        return enforce_single_lecture_image(section, state, unit, chunk_ids)

    try:
        section = generate_lecture_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        if not allow_generation_fallback(state, provider_mode=settings.provider_mode):
            raise
        section = build_lecture_unit_spec_fallback(state, unit, chunk_ids)
    return enforce_single_lecture_image(section, state, unit, chunk_ids)


def generate_lecture_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> LectureSection:
    unit_spec_id = f"lecture_{unit.id}"
    prompt = build_unit_spec_prompt("lecture", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(LectureSection, llm_service.generate_structured(prompt=prompt, schema=LectureSection))
