from typing import cast

from app.core.config import get_settings
from app.core.fallback import allow_generation_fallback
from app.generators.common.unit_prompt_builder import build_unit_spec_prompt
from app.generators.unit_specs.fallback_interactive_html import build_interactive_html_unit_spec_fallback
from app.schemas.outline import OutlineUnit
from app.schemas.specs import InteractiveHtmlSectionSpec
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def build_interactive_html_unit_spec(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    settings = get_settings()
    if settings.provider_mode == "stub":
        return build_interactive_html_unit_spec_fallback(state, unit, chunk_ids)

    try:
        return generate_interactive_html_unit_spec_with_llm(state, unit, chunk_ids)
    except Exception:
        if not allow_generation_fallback(state, provider_mode=settings.provider_mode):
            raise
        return build_interactive_html_unit_spec_fallback(state, unit, chunk_ids)


def generate_interactive_html_unit_spec_with_llm(
    state: ContentGenerationState, unit: OutlineUnit, chunk_ids: list[str]
) -> InteractiveHtmlSectionSpec:
    unit_spec_id = unit.id
    prompt = build_unit_spec_prompt("interactive_html", state, unit, unit_spec_id, chunk_ids)
    llm_service = get_llm_service()
    return cast(InteractiveHtmlSectionSpec, llm_service.generate_structured(prompt=prompt, schema=InteractiveHtmlSectionSpec))
