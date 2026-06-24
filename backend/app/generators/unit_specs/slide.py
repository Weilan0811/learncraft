from typing import cast

from app.core.config import get_settings
from app.core.fallback import allow_generation_fallback
from app.generators.common.unit_prompt_builder import build_unit_spec_prompt
from app.generators.unit_specs.fallback_slide import build_slide_unit_spec_fallback
from app.generators.unit_specs.slide_normalizer import normalize_slide_spec
from app.schemas.outline import OutlineUnit
from app.schemas.specs import SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def build_slide_unit_spec(state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]) -> SlideSpecPage:
    settings = get_settings()
    if settings.provider_mode == "stub":
        return normalize_slide_spec(build_slide_unit_spec_fallback(state, unit, chunk_ids), unit, state)

    try:
        raw_spec = generate_slide_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        if not allow_generation_fallback(state, provider_mode=settings.provider_mode):
            raise
        raw_spec = build_slide_unit_spec_fallback(state, unit, chunk_ids)
    return normalize_slide_spec(raw_spec, unit, state)


def generate_slide_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> SlideSpecPage:
    unit_spec_id = f"slide_{unit.id}"
    prompt = build_unit_spec_prompt("slide_deck", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(SlideSpecPage, llm_service.generate_structured(prompt=prompt, schema=SlideSpecPage))
