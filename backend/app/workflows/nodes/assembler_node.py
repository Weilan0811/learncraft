from app.schemas.specs import LectureSection, LectureSpec, SlideDeckSpec, SlideSpecPage
from app.schemas.state import ContentGenerationState
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def assemble_content_spec(state: ContentGenerationState) -> dict[str, object]:
    if state.outline is None:
        return {"errors": state.errors + ["outline is missing"], "current_node": "assemble_content_spec"}
    ordered_results = [state.unit_results[unit_id] for unit_id in state.pending_unit_ids if unit_id in state.unit_results]
    if state.content_type == "slide_deck":
        slides = [result.unit_spec for result in ordered_results if isinstance(result.unit_spec, SlideSpecPage)]
        content_spec = SlideDeckSpec(
            id=f"deck_{state.request_id}",
            title=state.outline.title,
            metadata={"language": (state.normalized_request or {}).get("language", "zh-CN"), "outline_id": state.outline.id},
            slides=slides,
        )
    else:
        sections = [result.unit_spec for result in ordered_results if isinstance(result.unit_spec, LectureSection)]
        content_spec = LectureSpec(
            id=f"lecture_{state.request_id}",
            title=state.outline.title,
            metadata={"language": (state.normalized_request or {}).get("language", "zh-CN"), "outline_id": state.outline.id},
            objectives=state.outline.learning_objectives,
            sections=sections,
        )
    return {
        "content_spec": content_spec,
        "current_node": "assemble_content_spec",
        "progress": ensure_monotonic_progress(
            state.progress,
            build_progress(
                stage="assembling_content",
                current_node="assemble_content_spec",
                completed_units=len(ordered_results),
                total_units=len(state.pending_unit_ids),
            ),
        ),
    }


__all__ = ["assemble_content_spec"]
