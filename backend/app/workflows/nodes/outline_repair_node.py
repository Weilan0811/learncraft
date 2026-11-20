import json
import time
from pathlib import Path

from app.core.config import get_settings
from app.core.telemetry import drain_provider_metrics
from app.generators.common.retrieval_formatter import format_retrieval_results
from app.schemas.outline import Outline
from app.schemas.state import ContentGenerationState
from app.services.llm_service import get_llm_service


def repair_outline(state: ContentGenerationState) -> dict[str, object]:
    retry_counts = {**state.retry_counts, "outline_repair": state.retry_counts.get("outline_repair", 0) + 1}
    settings = get_settings()
    record = {"attempt": retry_counts["outline_repair"],
              "validation_errors": (state.outline_validation_report or {}).get("errors", []),
              "provider": settings.text_provider, "model": settings.text_model}
    outline = state.outline.model_copy(deep=True)
    if settings.provider_mode == "stub":
        record["error"] = "非真实模型模式不执行大纲修复。"
    else:
        template = (Path(__file__).resolve().parents[2] / "prompts/planner/repair_outline.md").read_text(encoding="utf-8")
        prompt = template.format(
            request_json=json.dumps({"topic": state.topic, "user_prompt": state.user_prompt,
                "content_type": state.content_type, "generation_options": state.normalized_request}, ensure_ascii=False),
            outline_json=outline.model_dump_json(), errors_json=json.dumps(record["validation_errors"], ensure_ascii=False),
            retrieval_results=format_retrieval_results(state.planning_chunks))
        service = get_llm_service()
        started = time.perf_counter()
        try:
            outline = service.generate_structured(prompt=prompt, schema=Outline)
        except Exception as exc:
            record["error"] = str(exc)
        finally:
            record["seconds"] = time.perf_counter() - started
            record["usage"] = getattr(service, "last_usage", {})
            record["model_calls"] = [metric.model_dump(mode="json") for metric in drain_provider_metrics(
                task_id=state.request_id, node="repair_outline")]
    outline.metadata = {**outline.metadata,
        "generation": state.outline.metadata.get("generation", {}),
        "planner_source": state.outline.metadata.get("planner_source", "llm"), "validation_repair": record}
    return {"outline": outline, "retry_counts": retry_counts, "current_node": "repair_outline"}
