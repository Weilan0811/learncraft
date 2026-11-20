import json
import time
from pathlib import Path

from app.core.config import get_settings
from app.core.telemetry import drain_provider_metrics
from app.generators.common.retrieval_formatter import retrieval_snapshot
from app.schemas.retrieval import KnowledgeQueryPlan
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.workflows.nodes.helpers import build_progress, current_outline_unit, request_from_state, unit_progress


def retrieve_for_planning(state: ContentGenerationState) -> dict[str, object]:
    request = request_from_state(state)
    plan = None
    plan_metadata = {}
    if get_settings().kb_provider == "local":
        template = (Path(__file__).resolve().parents[2] / "prompts/retrieval/planning_queries.md").read_text(encoding="utf-8")
        inputs = {"topic": request.topic, "user_prompt": request.user_prompt,
                  "system_prompt": request.system_prompt, "content_type": request.content_type,
                  "generation_options": state.normalized_request or {},
                  "attachment_names": [a.filename for a in request.attachments]}
        llm_service = get_llm_service()
        started = time.perf_counter()
        plan = llm_service.generate_structured(
            prompt=template.format(request_json=json.dumps(inputs, ensure_ascii=False, indent=2)),
            schema=KnowledgeQueryPlan,
        )
        plan_metadata = {"seconds": time.perf_counter() - started,
                         "usage": getattr(llm_service, "last_usage", {}),
                         "model_calls": [metric.model_dump(mode="json") for metric in drain_provider_metrics(
                             task_id=state.request_id, node="retrieve_for_planning")],
                         "provider": get_settings().text_provider,
                         "model": get_settings().text_model}
    queries = [item.query for item in plan.queries] if plan else []
    service = get_rag_service()
    result = (service.retrieve(request, stage="planning", queries=queries)
              if plan else service.retrieve(request, stage="planning"))
    return {
        "planning_query_plan": plan.model_dump() if plan else {},
        "retrieval_records": {**state.retrieval_records, "planning": {
            "queries": queries, "results": result.query_results, "status": result.status.model_dump(),
            "query_planning": plan_metadata,
            "context": retrieval_snapshot(result.chunks),
        }},
        "retrieved_chunks": result.chunks,
        "planning_chunks": result.chunks,
        "retrieval_status": result.status,
        "current_node": "retrieve_for_planning",
        "progress": build_progress(stage="retrieving", current_node="retrieve_for_planning"),
    }


def retrieve_for_unit(state: ContentGenerationState) -> dict[str, object]:
    unit = current_outline_unit(state)
    request = request_from_state(state)
    queries = unit.retrieval_queries
    result = get_rag_service().retrieve(request, stage="generation", queries=queries)
    chunks = result.chunks or state.planning_chunks
    retrieval_status = result.status if result.status.state == "failed" else state.retrieval_status
    unit_context_map = dict(state.unit_context_map)
    unit_context_map[unit.id] = chunks
    return {
        "retrieval_records": {**state.retrieval_records, unit.id: {
            "queries": queries, "results": result.query_results,
            "status": result.status.model_dump(),
            "used_planning_context": not bool(result.chunks) and bool(state.planning_chunks),
            "context": retrieval_snapshot(chunks),
        }},
        "current_unit_id": unit.id,
        "current_unit_context": chunks,
        "unit_context_map": unit_context_map,
        "retrieval_status": retrieval_status,
        "current_node": "retrieve_for_unit",
        "progress": unit_progress(state, "retrieving_unit", current_node="retrieve_for_unit"),
    }


__all__ = ["retrieve_for_planning", "retrieve_for_unit"]
