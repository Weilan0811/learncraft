import json
import os

from app.content_types.registry import get_content_type_profile
from app.generators.common.retrieval_formatter import format_retrieval_results
from app.schemas.outline import OutlineUnit
from app.schemas.state import ContentGenerationState


def build_unit_spec_prompt(
    content_type: str,
    state: ContentGenerationState,
    unit: OutlineUnit,
    unit_spec_id: str,
    chunk_ids: list[str] | None = None,
) -> str:
    template_path = get_unit_spec_template_path(content_type)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    return template.format(
        unit_spec_id=unit_spec_id,
        topic=state.topic,
        user_prompt=state.user_prompt,
        outline_unit=json.dumps(unit.model_dump(mode="json"), ensure_ascii=False, indent=2),
        generation_options=json.dumps(state.normalized_request or {}, ensure_ascii=False, indent=2),
        retrieval_results=format_retrieval_results(state.current_unit_context),
        chunk_ids=json.dumps(chunk_ids or unit.source_chunk_ids, ensure_ascii=False),
    )


def build_unit_spec_repair_prompt(
    content_type: str,
    state: ContentGenerationState,
    unit: OutlineUnit,
    unit_spec_id: str,
    chunk_ids: list[str],
    validation_errors: list[str],
) -> str:
    base_prompt = build_unit_spec_prompt(content_type, state, unit, unit_spec_id, chunk_ids)
    invalid_spec = state.current_unit_spec.model_dump(mode="json") if state.current_unit_spec else None
    repair_contract = {
        "content_type": content_type,
        "unit_spec_id": unit_spec_id,
        "outline_unit_id": unit.id,
        "outline_unit_order": unit.order,
        "validation_errors": validation_errors,
        "invalid_unit_spec": invalid_spec,
    }
    if content_type == "interactive_html":
        id_contract = {
            "section_id": unit_spec_id,
            "title": unit.title,
            "learning_goal": unit.goal,
        }
    else:
        id_contract = {
            "id": unit_spec_id,
            "outline_unit_id": unit.id,
            "order": unit.order,
        }
    return (
        f"{base_prompt}\n\n"
        "## Repair context\n"
        "The previous unit spec failed workflow validation. Regenerate the full unit spec from scratch, using the same schema.\n"
        "Use the validation errors and invalid unit spec below only as diagnostic input. Do not copy invalid values unless they satisfy the contract.\n"
        "Hard contract for this unit:\n"
        f"{json.dumps(id_contract, ensure_ascii=False, indent=2)}\n\n"
        "Validation errors and previous invalid output:\n"
        f"{json.dumps(repair_contract, ensure_ascii=False, indent=2)}\n\n"
        "Return only corrected JSON for the requested schema."
    )


def get_unit_spec_template_path(content_type: str) -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "generator")
    profile = get_content_type_profile(content_type)
    return os.path.join(prompts_dir, profile.unit_spec_prompt_name)
