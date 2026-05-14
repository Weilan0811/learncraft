from app.schemas.state import ContentGenerationState
from app.services.rag_service import get_rag_service
from app.workflows.nodes.helpers import build_progress, current_outline_unit, request_from_state, unit_progress


def retrieve_for_planning(state: ContentGenerationState) -> dict[str, object]:
    request = request_from_state(state)
    service = get_rag_service()
    chunks = service.retrieve(request, stage="planning")
    diagnostics = getattr(service, "last_diagnostics", {})
    return {
        "retrieved_chunks": chunks,
        "planning_chunks": chunks,
        "workflow_errors": [
            *state.workflow_errors,
            *(
                [
                    {
                        "stage": "retrieval",
                        "code": "empty_retrieval",
                        "message": "Knowledge retrieval returned no chunks.",
                        "detail": diagnostics,
                        "recoverable": True,
                    }
                ]
                if not chunks
                else []
            ),
        ],
        "current_node": "retrieve_for_planning",
        "progress": build_progress(stage="retrieving", current_node="retrieve_for_planning"),
    }


def retrieve_for_unit(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    request = request_from_state(state)
    section_hint = "\n".join([unit.title, unit.core_message, *unit.retrieval_queries])
    service = get_rag_service()
    chunks = service.retrieve(request, stage="generation", section_hint=section_hint)
    diagnostics = getattr(service, "last_diagnostics", {})
    if not chunks:
        chunks = state.planning_chunks
    workflow_errors = list(state.workflow_errors)
    if not chunks:
        workflow_errors.append(
            {
                "stage": "retrieval",
                "code": "empty_unit_retrieval",
                "message": "Unit knowledge retrieval returned no chunks.",
                "detail": diagnostics,
                "recoverable": True,
            }
        )
    unit_context_map = dict(state.unit_context_map)
    unit_context_map[unit.id] = chunks
    return {
        "current_unit_id": unit.id,
        "current_unit_context": chunks,
        "unit_context_map": unit_context_map,
        "workflow_errors": workflow_errors,
        "current_node": "retrieve_for_unit",
        "progress": unit_progress(state, "retrieving_unit", current_node="retrieve_for_unit"),
    }


__all__ = ["retrieve_for_planning", "retrieve_for_unit"]
