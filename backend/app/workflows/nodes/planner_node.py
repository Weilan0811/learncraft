import json
import os
from typing import cast

from app.core.config import get_settings
from app.schemas.outline import Outline, OutlineSection, OutlineUnit
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service
from app.workflows.nodes.helpers import build_progress


def plan_outline(state: ContentGenerationState) -> dict[str, object]:
    settings = get_settings()

    if settings.provider_mode == "stub":
        outline = _build_fallback_outline(state, reason="provider_mode=stub")
        return _planner_success(state, outline, source="stub")

    try:
        outline = _generate_outline_with_llm(state)
        return _planner_success(state, outline, source="llm")
    except Exception as exc:
        outline = _build_fallback_outline(state, reason=str(exc))
        return _planner_success_with_warning(state, outline, exc)


def _generate_outline_with_llm(state: ContentGenerationState) -> Outline:
    prompt = _build_planner_prompt(state)
    llm_service = get_llm_service()
    return cast(Outline, llm_service.generate_structured(prompt=prompt, schema=Outline))


def _build_planner_prompt(state: ContentGenerationState) -> str:
    template_path = _get_prompt_template_path(state.content_type)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    retrieval_results = _format_retrieval_results(state.planning_chunks)
    generation_options = json.dumps(state.normalized_request, ensure_ascii=False, indent=2)

    return template.format(
        topic=state.topic,
        user_prompt=state.user_prompt,
        generation_options=generation_options,
        retrieval_results=retrieval_results,
    )


def _get_prompt_template_path(content_type: str) -> str:
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "planner")
    if content_type == "slide_deck":
        return os.path.join(prompts_dir, "slide_outline.md")
    return os.path.join(prompts_dir, "lecture_outline.md")


def _format_retrieval_results(chunks: list) -> str:
    if not chunks:
        return "No retrieval results."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        chunk_id = getattr(chunk, "id", f"chunk_{i}")
        source_title = getattr(chunk, "source_title", "")
        score = getattr(chunk, "score", 0.0)
        content = getattr(chunk, "content", "")[:500]
        formatted.append(f"[chunk_id={chunk_id}]")
        if source_title:
            formatted.append(f"source_title: {source_title}")
        formatted.append(f"score: {score}")
        formatted.append(f"content: {content}")
        formatted.append("")

    return "\n".join(formatted)


def _build_fallback_outline(state: ContentGenerationState, reason: str | None = None) -> Outline:
    chunk_ids = [chunk.id for chunk in state.planning_chunks]
    unit_type = "slide" if state.content_type == "slide_deck" else "section"

    options = state.normalized_request or {}
    fallback_default = 6 if state.content_type == "slide_deck" else 4
    max_count_key = "max_slide_count" if state.content_type == "slide_deck" else "max_section_count"
    legacy_count_key = "slide_count" if state.content_type == "slide_deck" else "section_count"
    max_units = options.get(max_count_key) or options.get(legacy_count_key) or (12 if state.content_type == "slide_deck" else 8)
    units_count = max(1, min(int(max_units or fallback_default), fallback_default))

    units = []
    sections = []

    for i in range(1, units_count + 1):
        unit_title = f"{state.topic} - part {i}" if units_count > 1 else state.topic
        unit_id = f"unit_{str(i).zfill(3)}"

        unit = OutlineUnit(
            id=unit_id,
            order=i,
            unit_type=unit_type,
            title=unit_title,
            goal=f"Build understanding of {unit_title}.",
            core_message=f"{unit_title} is an important part of understanding {state.topic}.",
            key_points=[f"{unit_title} key point 1", f"{unit_title} key point 2", f"{unit_title} key point 3"],
            visual_strategy="title-content-visual",
            retrieval_queries=[state.topic, unit_title],
            source_chunk_ids=chunk_ids,
        )
        units.append(unit)

        section = OutlineSection(
            id=f"sec_{str(i).zfill(3)}",
            title=unit_title,
            goal=unit.goal,
            key_points=unit.key_points,
            estimated_minutes=5 if state.content_type == "lecture" else None,
            citations=chunk_ids,
        )
        sections.append(section)

    metadata = {"created_by": "planner_node", "stub": True}
    if reason:
        metadata["fallback_reason"] = reason

    return Outline(
        id=f"outline_{state.request_id}",
        content_type=state.content_type,
        title=state.topic,
        audience=options.get("audience", "general learners"),
        learning_objectives=[f"Understand the core concepts of {state.topic}", f"Apply basic ideas from {state.topic}"],
        units=units,
        sections=sections,
        metadata=metadata,
    )


def _planner_success(state: ContentGenerationState, outline: Outline, source: str) -> dict[str, object]:
    for unit in outline.units:
        if not unit.retrieval_queries:
            unit.retrieval_queries = [state.topic, unit.title]
    return {
        "outline": outline,
        "current_node": "plan_outline",
        "progress": build_progress(stage="planning", current_node="plan_outline"),
    }


def _planner_success_with_warning(state: ContentGenerationState, outline: Outline, exc: Exception) -> dict[str, object]:
    result = _planner_success(state, outline, source="fallback")
    if "workflow_errors" not in result:
        result["workflow_errors"] = []
    result["workflow_errors"].append(
        {
            "stage": "plan_outline",
            "code": type(exc).__name__,
            "message": str(exc),
            "detail": {"recovery": "used fallback outline"},
            "recoverable": True,
        }
    )
    return result


__all__ = ["plan_outline"]
