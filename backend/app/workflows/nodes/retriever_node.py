from app.schemas.state import ContentGenerationState
from app.services.rag_service import get_rag_service
from app.workflows.nodes.helpers import current_outline_unit, request_from_state


def retrieve_for_planning(state: ContentGenerationState) -> dict[str, object]:
    request = request_from_state(state)
    chunks = get_rag_service().retrieve(request, stage="planning")
    return {
        "retrieved_chunks": chunks,
        "planning_chunks": chunks,
        "current_node": "retrieve_for_planning",
        "progress": {"current_stage": "retrieving", "percent": 15},
    }


def retrieve_for_unit(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    request = request_from_state(state)
    section_hint = "\n".join([unit.title, unit.core_message, *unit.retrieval_queries])
    chunks = get_rag_service().retrieve(request, stage="generation", section_hint=section_hint)
    if not chunks:
        chunks = state.planning_chunks
    unit_context_map = dict(state.unit_context_map)
    unit_context_map[unit.id] = chunks
    return {
        "current_unit_id": unit.id,
        "current_unit_context": chunks,
        "unit_context_map": unit_context_map,
        "current_node": "retrieve_for_unit",
        "progress": {
            "current_stage": "retrieving_unit",
            "current_unit_id": state.current_unit_id,
            "completed_units": len(state.completed_unit_ids),
            "total_units": len(state.pending_unit_ids),
            "percent": 45,
        },
    }


__all__ = ["retrieve_for_planning", "retrieve_for_unit"]
