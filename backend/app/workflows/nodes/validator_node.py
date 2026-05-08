from app.schemas.elements import ImageElement, MindmapElement
from app.schemas.specs import ElementReferenceBlock, SlideDeckSpec, SlideSpecPage
from app.schemas.state import ContentGenerationState
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
        if len(unit_ids) != len(set(unit_ids)):
            errors.append("outline unit ids must be unique")
        for unit in state.outline.units:
            if not unit.title or not unit.goal or not unit.core_message:
                errors.append(f"outline unit {unit.id} is missing required text fields")
            if not unit.retrieval_queries:
                errors.append(f"outline unit {unit.id} is missing retrieval_queries")
            unsupported = [item.type for item in unit.recommended_elements if item.type not in SUPPORTED_WORKFLOW_ELEMENTS]
            if unsupported:
                errors.append(f"outline unit {unit.id} has unsupported MVP elements: {unsupported}")
    return {
        "outline_validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_outline",
        "progress": ensure_monotonic_progress(state.progress, build_progress(stage="validating_outline", current_node="validate_outline")),
    }


def route_after_outline_validation(state: ContentGenerationState) -> str:
    report = state.outline_validation_report or {}
    return "pass" if report.get("passed") else "fail"


def validate_unit_spec(state: ContentGenerationState) -> dict[str, object]:
    errors: list[str] = []
    unit = current_outline_unit(state)
    unit_spec = state.current_unit_spec
    if unit_spec is None:
        errors.append("current_unit_spec is missing")
    else:
        if unit_spec.outline_unit_id != unit.id:
            errors.append("unit_spec.outline_unit_id does not match current unit")
        required_ids = {item.element_id for item in unit_spec.required_elements}
        if len(required_ids) != len(unit_spec.required_elements):
            errors.append("required element ids must be unique")
        for item in unit_spec.required_elements:
            if item.type not in SUPPORTED_WORKFLOW_ELEMENTS:
                errors.append(f"unsupported required element type: {item.type}")
        for element_id in element_ref_ids(unit_spec):
            if element_id not in required_ids:
                errors.append(f"element_ref {element_id} is missing from required_elements")
        if isinstance(unit_spec, SlideSpecPage):
            if not unit_spec.layout_hints.get("supported_renderer"):
                errors.append("slide unit_spec.layout_hints.supported_renderer is missing")
            roles = [element.metadata.get("role") for element in unit_spec.elements]
            if "title" not in roles:
                errors.append("slide unit spec is missing a title role element")
            if "body" not in roles:
                errors.append("slide unit spec is missing a body role element")
    return {
        "spec_validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_unit_spec",
        "progress": unit_progress(state, "validating_unit_spec", current_node="validate_unit_spec"),
    }


def route_after_unit_spec_validation(state: ContentGenerationState) -> str:
    report = state.spec_validation_report or {}
    return "pass" if report.get("passed") else "fail"


def validate_unit(state: ContentGenerationState) -> dict[str, object]:
    unit_spec = state.current_unit_spec
    element_lookup = {element.id: element for element in state.elements}
    errors: list[str] = []
    if unit_spec is None:
        errors.append("current_unit_spec is missing")
    else:
        for required in unit_spec.required_elements:
            element = element_lookup.get(required.element_id)
            if element is None and required.priority == "high":
                errors.append(f"required element {required.element_id} is missing")
            if isinstance(element, ImageElement) and (not element.prompt or not element.asset_url or not element.alt_text):
                errors.append(f"image element {element.id} is incomplete")
            if isinstance(element, MindmapElement) and not element.markdown.startswith("#"):
                errors.append(f"mindmap element {element.id} must start with #")
    return {
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_unit",
        "progress": unit_progress(state, "validating_unit", current_node="validate_unit"),
    }


def route_after_unit_validation(state: ContentGenerationState) -> str:
    report = state.validation_report or {}
    return "pass" if report.get("passed") else "fail"


def validate_content(state: ContentGenerationState) -> dict[str, object]:
    errors: list[str] = []
    if state.content_spec is None:
        errors.append("content_spec is missing")
    if state.outline is None:
        errors.append("outline is missing")
    element_lookup = {element.id: element for element in state.elements}
    if state.content_spec is not None:
        for element_id in content_element_ref_ids(state.content_spec):
            if element_id not in element_lookup:
                errors.append(f"content element_ref {element_id} is missing")
        if isinstance(state.content_spec, SlideDeckSpec):
            for slide in state.content_spec.slides:
                if not slide.design_intent:
                    errors.append(f"slide {slide.id} is missing design_intent")
                if not slide.speaker_notes:
                    errors.append(f"slide {slide.id} is missing speaker_notes")
                if not slide.layout_hints.get("supported_renderer"):
                    errors.append(f"slide {slide.id} is missing scenekit renderer hint")
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
