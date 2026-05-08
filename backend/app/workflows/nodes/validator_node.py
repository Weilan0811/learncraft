from typing import cast

from app.schemas.elements import ImageElement, MindmapElement
from app.schemas.outline import OutlineUnit
from app.schemas.specs import ElementReferenceBlock, LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import (
    SUPPORTED_WORKFLOW_ELEMENTS,
    content_element_ref_ids,
    current_outline_unit,
    element_ref_ids,
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
        
        orders = [unit.order for unit in state.outline.units]
        if sorted(orders) != list(range(1, len(orders) + 1)):
            errors.append("outline unit orders must be sequential from 1")
        
        if state.outline.content_type != state.content_type:
            errors.append("outline.content_type must match request content_type")
        
        expected_unit_type = "slide" if state.content_type == "slide_deck" else "section"
        for unit in state.outline.units:
            if not unit.title or not unit.goal or not unit.core_message:
                errors.append(f"outline unit {unit.id} is missing required text fields")
            
            if not unit.retrieval_queries:
                errors.append(f"outline unit {unit.id} is missing retrieval_queries")
            
            if unit.unit_type != expected_unit_type:
                errors.append(f"outline unit {unit.id} has incorrect unit_type: expected {expected_unit_type}")
            
            if not unit.source_chunk_ids and state.planning_chunks:
                errors.append(f"outline unit {unit.id} should reference planning chunks")
    
    return {
        "outline_validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_outline",
        "progress": {"current_stage": "validating_outline", "percent": 30},
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
        
        if unit_spec.id != f"{'slide' if state.content_type == 'slide_deck' else 'lecture'}_{unit.id}":
            errors.append("unit_spec.id format is incorrect")
        
        if unit_spec.order != unit.order:
            errors.append("unit_spec.order must match outline unit order")
        
        if isinstance(unit_spec, LectureSection):
            if not unit_spec.title or not unit_spec.summary or not unit_spec.learning_goal:
                errors.append(f"lecture section {unit_spec.id} is missing required fields")
            
            if not unit_spec.blocks:
                errors.append(f"lecture section {unit_spec.id} must have at least one block")
            
            if not any(isinstance(block, ElementReferenceBlock) for block in unit_spec.blocks):
                text_blocks = [b for b in unit_spec.blocks if b.type == "text"]
                if not text_blocks:
                    errors.append(f"lecture section {unit_spec.id} must have at least one text block")
        
        if isinstance(unit_spec, SlideSpecPage):
            if not unit_spec.title or not unit_spec.core_message:
                errors.append(f"slide {unit_spec.id} is missing required fields")
            
            if not unit_spec.elements:
                errors.append(f"slide {unit_spec.id} must have at least one element")
            
            text_elements = [e for e in unit_spec.elements if e.type == "text"]
            if len(text_elements) < 2:
                errors.append(f"slide {unit_spec.id} should have title and body text elements")
        
        required_ids = {item.element_id for item in unit_spec.required_elements}
        if len(required_ids) != len(unit_spec.required_elements):
            errors.append("required element ids must be unique")
        
        for item in unit_spec.required_elements:
            if item.type not in SUPPORTED_WORKFLOW_ELEMENTS:
                errors.append(f"unsupported required element type: {item.type}")
            
            if not item.source_chunk_ids and state.current_unit_context:
                errors.append(f"required element {item.element_id} should reference source chunks")
        
        for element_id in element_ref_ids(unit_spec):
            if element_id not in required_ids:
                errors.append(f"element_ref {element_id} is missing from required_elements")
    
    return {
        "spec_validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_unit_spec",
        "progress": unit_progress(state, "validating_unit_spec", 60),
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
        "progress": unit_progress(state, "validating_unit", 80),
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
        
        if isinstance(content_type, SlideDeckSpec):
            if not content_type.slides:
                errors.append("slide deck spec must have at least one slide")
            
            slide_ids = [slide.id for slide in content_type.slides]
            if len(slide_ids) != len(set(slide_ids)):
                errors.append("slide ids must be unique")
            
            slide_orders = [slide.order for slide in content_type.slides if slide.order]
            if slide_orders and sorted(slide_orders) != list(range(1, len(slide_orders) + 1)):
                errors.append("slide orders must be sequential from 1")
    
    if state.outline is not None and state.content_spec is not None:
        outline_units = set(unit.id for unit in state.outline.units)
        spec_units = set()
        
        if isinstance(state.content_spec, LectureSpec):
            spec_units = {sec.outline_unit_id for sec in state.content_spec.sections if sec.outline_unit_id}
        elif isinstance(state.content_spec, SlideDeckSpec):
            spec_units = {slide.outline_unit_id for slide in state.content_spec.slides if slide.outline_unit_id}
        
        if outline_units != spec_units:
            errors.append("content_spec must reference all outline units")
    
    return {
        "validation_report": {"passed": not errors, "errors": errors},
        "errors": state.errors + errors,
        "current_node": "validate_content",
        "progress": {"current_stage": "validating_content", "percent": 94},
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
