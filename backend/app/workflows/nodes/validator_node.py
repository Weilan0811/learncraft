from typing import cast
import re
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.elements import ImageElement, MindmapElement
from app.schemas.specs import (
    ElementReferenceBlock,
    IMAGE_TEXT_REQUIRED_ROLES,
    InteractiveHtmlSectionSpec,
    InteractiveHtmlSpec,
    LectureSection,
    LectureSpec,
    SlideDeckSpec,
    SlideSpecPage,
    VISUAL_SUMMARY_REQUIRED_ROLES,
)
from app.schemas.state import ContentGenerationState, TaskStreamEvent
from app.validators.interactive_html_validator import (
    validate_content as validate_interactive_html_content,
)
from app.validators.interactive_html_validator import (
    validate_unit_spec as validate_interactive_html_unit_spec,
)
from app.workflows.nodes.helpers import (
    SUPPORTED_WORKFLOW_ELEMENTS,
    build_progress,
    content_element_ref_ids,
    current_outline_unit,
    element_ref_ids,
    ensure_monotonic_progress,
    unit_progress,
)


def validate_outline(state: ContentGenerationState) -> dict[str, object]:
    errors: list[str] = []
    if state.outline is None:
        errors.append("outline is missing")
    else:
        unit_ids = [unit.id for unit in state.outline.units]

        if not state.outline.units:
            errors.append("outline.units is empty")
        options = state.normalized_request or {}
        count_key = "max_slide_count" if state.content_type == "slide_deck" else "max_section_count"
        limit = options.get(count_key)
        if limit is not None and len(state.outline.units) > int(limit):
            errors.append(f"outline.units exceeds {count_key}={limit}")
        available_ids = {chunk.id for chunk in state.planning_chunks}
        if state.outline.metadata.get("insufficient_knowledge"):
            errors.append(f"资料不足：{state.outline.metadata['insufficient_knowledge']}")

        if len(unit_ids) != len(set(unit_ids)):
            errors.append("outline unit ids must be unique")

        orders = [unit.order for unit in state.outline.units]
        if sorted(orders) != list(range(1, len(orders) + 1)):
            errors.append("outline unit orders must be sequential from 1")

        if state.outline.content_type != state.content_type:
            errors.append("outline.content_type must match request content_type")

        if state.content_type == "slide_deck":
            expected_unit_type = "slide"
        elif state.content_type == "interactive_html":
            expected_unit_type = "interactive_section"
        else:
            expected_unit_type = "section"
        for unit in state.outline.units:
            if not unit.title or not unit.goal or not unit.core_message:
                errors.append(f"outline unit {unit.id} is missing required text fields")

            if not unit.retrieval_queries or any(not query.strip() for query in unit.retrieval_queries):
                errors.append(f"outline unit {unit.id} is missing retrieval_queries")
            if set(unit.source_chunk_ids) - available_ids:
                errors.append(f"outline unit {unit.id} references unavailable chunks")

            if unit.unit_type != expected_unit_type:
                errors.append(f"outline unit {unit.id} has incorrect unit_type: expected {expected_unit_type}")

            if not unit.source_chunk_ids and state.planning_chunks:
                errors.append(f"outline unit {unit.id} should reference planning chunks")
        for section in state.outline.sections:
            if set(section.citations) - available_ids:
                errors.append(f"outline section {section.id} references unavailable chunks")

    previous_errors = (state.outline_validation_report or {}).get("errors", [])
    result = {
        "outline_validation_report": {"passed": not errors, "errors": errors},
        "errors": [error for error in state.errors if error not in previous_errors] + errors,
        "current_node": "validate_outline",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(stage="validating_outline", current_node="validate_outline"),
        ),
    }
    if not errors and not any(event.type == "outline_ready" for event in state.stream_events):
        result["stream_events"] = [*state.stream_events, TaskStreamEvent(
            event_id=f"event_{uuid4().hex[:12]}", task_id=state.request_id,
            type="outline_ready", payload={"outline_id": state.outline.id,
                "unit_count": len(state.outline.units),
                "source": state.outline.metadata.get("planner_source", "llm")},
            created_at=datetime.now(UTC).isoformat())]
    return result


def route_after_outline_validation(state: ContentGenerationState) -> str:
    report = state.outline_validation_report or {}
    if report.get("passed"):
        return "pass"
    if state.outline is not None and state.retry_counts.get("outline_repair", 0) < 1:
        return "repair"
    return "fail"


def validate_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    errors: list[str] = []
    unit = current_outline_unit(state)
    unit_spec = state.current_unit_spec

    if unit_spec is None:
        errors.append("current_unit_spec is missing")
    else:
        if isinstance(unit_spec, InteractiveHtmlSectionSpec):
            if unit_spec.section_id != unit.id:
                errors.append("unit_spec.section_id does not match current unit")
        else:
            if unit_spec.outline_unit_id != unit.id:
                errors.append("unit_spec.outline_unit_id does not match current unit")

            if unit_spec.id != f"{'slide' if state.content_type == 'slide_deck' else 'lecture'}_{unit.id}":
                errors.append("unit_spec.id format is incorrect")

            if unit_spec.order != unit.order:
                errors.append("unit_spec.order must match outline unit order")

        if isinstance(unit_spec, LectureSection):
            if not unit_spec.title or not unit_spec.summary or not unit_spec.learning_goal:
                errors.append(f"lecture section {unit_spec.id} is missing required fields")

            if not unit_spec.blocks:
                errors.append(f"lecture section {unit_spec.id} must have at least one block")

            image_specs = [item for item in unit_spec.required_elements if item.type == "image"]
            if len(image_specs) != 1:
                errors.append(f"lecture section {unit_spec.id} must declare exactly one image element")

            if not any(isinstance(block, ElementReferenceBlock) for block in unit_spec.blocks):
                text_blocks = [b for b in unit_spec.blocks if b.type == "text"]
                if not text_blocks:
                    errors.append(f"lecture section {unit_spec.id} must have at least one text block")

        if isinstance(unit_spec, InteractiveHtmlSectionSpec):
            if not unit_spec.title or not unit_spec.learning_goal:
                errors.append(f"interactive section {unit_spec.section_id} is missing required fields")

            report = validate_interactive_html_unit_spec(unit_spec)
            errors.extend([f"{issue.path}: {issue.message}" for issue in report.issues])

        if isinstance(unit_spec, SlideSpecPage):
            if not unit_spec.title or not unit_spec.core_message:
                errors.append(f"slide {unit_spec.id} is missing required fields")

            if not unit_spec.elements:
                errors.append(f"slide {unit_spec.id} must have at least one element")

            if unit_spec.layout not in ("image_text", "visual_summary"):
                errors.append(f"slide {unit_spec.id} has unsupported layout: {unit_spec.layout}")

            roles = [element.metadata.get("role") for element in unit_spec.elements]
            if "title" not in roles:
                errors.append("slide unit spec is missing a title role element")

            if unit_spec.layout == "image_text":
                missing = IMAGE_TEXT_REQUIRED_ROLES - set(roles)
                if missing:
                    errors.append(f"slide {unit_spec.id} image_text layout missing roles: {missing}")
                extra = set(str(role) for role in roles) - IMAGE_TEXT_REQUIRED_ROLES
                if extra:
                    errors.append(f"slide {unit_spec.id} image_text layout has unsupported roles: {extra}")
                card_roles = [role for role in roles if role in {"lead_card", "support_card"}]
                if card_roles.count("lead_card") != 1 or card_roles.count("support_card") != 1:
                    errors.append(f"slide {unit_spec.id} image_text layout must have exactly two text cards")
                for element in unit_spec.elements:
                    if element.metadata.get("role") in {"lead_card", "support_card"} and not element.metadata.get("display_label"):
                        errors.append(f"slide {unit_spec.id} {element.metadata.get('role')} display_label is missing")
                    if element.metadata.get("role") == "summary_text" and element.content and _has_summary_prefix(element.content):
                        errors.append(f"slide {unit_spec.id} summary_text must not include fixed summary prefix")
            elif unit_spec.layout == "visual_summary":
                missing = VISUAL_SUMMARY_REQUIRED_ROLES - set(roles)
                if missing:
                    errors.append(f"slide {unit_spec.id} visual_summary layout missing roles: {missing}")
                extra_cards = {"lead_card", "support_card", "explanation", "bullet_list", "takeaway"} & set(str(role) for role in roles)
                if extra_cards:
                    errors.append(f"slide {unit_spec.id} visual_summary layout has extra text card roles: {extra_cards}")
                for element in unit_spec.elements:
                    if element.metadata.get("role") == "summary_text" and element.content and _has_summary_prefix(element.content):
                        errors.append(f"slide {unit_spec.id} summary_text must not include fixed summary prefix")

            if not unit_spec.layout_hints.get("supported_renderer"):
                errors.append("slide unit_spec.layout_hints.supported_renderer is missing")

        required_elements = getattr(unit_spec, "required_elements", [])
        required_ids = {item.element_id for item in required_elements}
        if len(required_ids) != len(required_elements):
            errors.append("required element ids must be unique")

        for item in required_elements:
            if item.type not in SUPPORTED_WORKFLOW_ELEMENTS:
                errors.append(f"unsupported required element type: {item.type}")

            if not item.source_chunk_ids and state.current_unit_context:
                errors.append(f"required element {item.element_id} should reference source chunks")

        if required_elements:
            for element_id in element_ref_ids(unit_spec):
                if element_id not in required_ids:
                    errors.append(f"element_ref {element_id} is missing from required_elements")

    return {
        "spec_validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_unit_spec",
        "progress": unit_progress(state, "validating_unit_spec", current_node="validate_unit_spec"),
    }


def route_after_unit_spec_validation(state: ContentGenerationState) -> str:
    report = state.spec_validation_report or {}
    if report.get("passed"):
        return "pass"
    retry_key = f"unit_spec_repair:{state.current_unit_id or ''}"
    if state.retry_counts.get(retry_key, 0) < 1:
        return "repair"
    if bool((state.normalized_request or {}).get("allow_fallback", False)):
        return "fallback"
    return "fail"


def validate_unit(state: ContentGenerationState) -> dict[str, object]:
    unit_spec = state.current_unit_spec
    element_lookup = {element.id: element for element in state.elements}
    errors: list[str] = []

    if unit_spec is None:
        errors.append("current_unit_spec is missing")
    else:
        for required in getattr(unit_spec, "required_elements", []):
            element = element_lookup.get(required.element_id)

            if element is None and required.priority == "high":
                errors.append(f"required element {required.element_id} is missing")

            if element is not None:
                if element.status == "failed":
                    errors.append(f"element {element.id} generation failed")

                if isinstance(element, ImageElement):
                    if not element.prompt:
                        errors.append(f"image element {element.id} is missing prompt")
                    if not element.asset_url:
                        errors.append(f"image element {element.id} is missing asset_url")
                    if not element.alt_text:
                        errors.append(f"image element {element.id} is missing alt_text")

                if isinstance(element, MindmapElement):
                    if not element.markdown:
                        errors.append(f"mindmap element {element.id} is missing markdown")
                    else:
                        mindmap_errors = _validate_mindmap_markdown(element.markdown)
                        if mindmap_errors:
                            errors.extend([f"mindmap element {element.id}: {e}" for e in mindmap_errors])

    return {
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_unit",
        "progress": unit_progress(state, "validating_unit", current_node="validate_unit"),
    }


def _validate_mindmap_markdown(markdown: str) -> list[str]:
    errors = []
    lines = [line.rstrip() for line in markdown.splitlines() if line.strip()]

    if not lines:
        errors.append("markdown is empty")
        return errors

    if not lines[0].startswith("# "):
        errors.append("must start with one # root heading")

    root_count = sum(1 for line in lines if line.startswith("# ") and not line.startswith("## "))
    if root_count != 1:
        errors.append("must contain exactly one root heading")

    if any(line.startswith("####") for line in lines):
        errors.append("depth must be <= 3")

    if any("<" in line and ">" in line for line in lines):
        errors.append("must not contain HTML")

    first_level = [line for line in lines if line.startswith("## ") and not line.startswith("### ")]
    if len(first_level) < 3:
        errors.append("recommended to have at least 3 first-level branches")
    if len(first_level) > 6:
        errors.append("recommended to have at most 6 first-level branches")

    return errors


def _has_summary_prefix(text: str) -> bool:
    return bool(re.match(r"^\s*(核心点|总结|结论)\s*[:：]", text))


def route_after_unit_validation(state: ContentGenerationState) -> str:
    report = state.validation_report or {}
    return "pass" if report.get("passed") else "fail"


def validate_content(state: ContentGenerationState) -> dict[str, object]:
    errors: list[str] = []

    if state.content_spec is None:
        errors.append("content_spec is missing")

    if state.outline is None:
        errors.append("outline is missing")

    if state.elements is None:
        errors.append("elements list is missing")

    element_lookup = {element.id: element for element in (state.elements or [])}

    if state.content_spec is not None:
        content_type = cast(LectureSpec | SlideDeckSpec, state.content_spec)
        all_element_refs = content_element_ref_ids(content_type)

        for element_id in all_element_refs:
            if element_id not in element_lookup:
                errors.append(f"content element_ref {element_id} is missing")

        if isinstance(content_type, LectureSpec):
            if not content_type.sections:
                errors.append("lecture spec must have at least one section")

            section_ids = [sec.id for sec in content_type.sections]
            if len(section_ids) != len(set(section_ids)):
                errors.append("lecture section ids must be unique")

            outline_unit_ids = {unit.id for unit in state.outline.units} if state.outline else set()
            actual_outline_units = {sec.outline_unit_id for sec in content_type.sections if sec.outline_unit_id}
            if outline_unit_ids and actual_outline_units != outline_unit_ids:
                missing = outline_unit_ids - actual_outline_units
                extra = actual_outline_units - outline_unit_ids
                if missing:
                    errors.append(f"lecture sections missing outline unit references: {missing}")
                if extra:
                    errors.append(f"lecture sections has invalid outline unit references: {extra}")

        if isinstance(content_type, InteractiveHtmlSpec):
            if not content_type.sections:
                errors.append("interactive_html spec must have at least one section")

            section_ids = [sec.section_id for sec in content_type.sections]
            if len(section_ids) != len(set(section_ids)):
                errors.append("interactive_html section ids must be unique")
            report = validate_interactive_html_content(content_type)
            errors.extend([f"{issue.path}: {issue.message}" for issue in report.issues])

        if isinstance(content_type, SlideDeckSpec):
            if not content_type.slides:
                errors.append("slide deck spec must have at least one slide")

            slide_ids = [slide.id for slide in content_type.slides]
            if len(slide_ids) != len(set(slide_ids)):
                errors.append("slide ids must be unique")

            slide_orders = [slide.order for slide in content_type.slides if slide.order]
            if slide_orders and sorted(slide_orders) != list(range(1, len(slide_orders) + 1)):
                errors.append("slide orders must be sequential from 1")

            for slide in content_type.slides:
                if not slide.design_intent:
                    errors.append(f"slide {slide.id} is missing design_intent")
                if not slide.speaker_notes:
                    errors.append(f"slide {slide.id} is missing speaker_notes")
                if not slide.layout_hints.get("supported_renderer"):
                    errors.append(f"slide {slide.id} is missing scenekit renderer hint")

    if state.outline is not None and state.content_spec is not None:
        outline_units = {unit.id for unit in state.outline.units}
        spec_units: set[str | None] = set()

        if isinstance(state.content_spec, LectureSpec):
            spec_units = {sec.outline_unit_id for sec in state.content_spec.sections if sec.outline_unit_id}
        elif isinstance(state.content_spec, InteractiveHtmlSpec):
            spec_units = {sec.section_id for sec in state.content_spec.sections if sec.section_id}
        elif isinstance(state.content_spec, SlideDeckSpec):
            spec_units = {slide.outline_unit_id for slide in state.content_spec.slides if slide.outline_unit_id}

        if outline_units != spec_units:
            errors.append("content_spec must reference all outline units")

    return {
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_content",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(
                stage="validating_content",
                current_node="validate_content",
                completed_units=len(state.completed_unit_ids),
                total_units=len(state.pending_unit_ids),
            ),
        ),
    }


def route_after_content_validation(state: ContentGenerationState) -> str:
    report = state.validation_report or {}
    return "pass" if report.get("passed") else "fail"


__all__ = [
    "validate_outline",
    "route_after_outline_validation",
    "validate_unit_spec",
    "route_after_unit_spec_validation",
    "validate_unit",
    "route_after_unit_validation",
    "validate_content",
    "route_after_content_validation",
]
