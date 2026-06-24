from app.core.task import TaskStatus
from app.schemas.observability import GenerationMetric
from app.schemas.request import ContentGenerationRequest
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService

from tests.test_task_persistence import sqlite_url


def test_generation_metric_serializes_token_retry_and_fallback_fields() -> None:
    metric = GenerationMetric(
        task_id="task_metric",
        node="generate_unit_spec",
        unit_id="unit_001",
        provider="bailian",
        model="qwen3.5-flash",
        duration_ms=125,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        retry_count=1,
        fallback_used=True,
        fallback_reason="LLMGenerationError: schema mismatch",
    )

    payload = metric.model_dump(mode="json")

    assert payload["task_id"] == "task_metric"
    assert payload["node"] == "generate_unit_spec"
    assert payload["total_tokens"] == 30
    assert payload["retry_count"] == 1
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"] == "LLMGenerationError: schema mismatch"


def test_stub_workflow_persists_node_metrics(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False)
    service = PersistentTaskService(repository=repository)
    created = service.create_task(
        ContentGenerationRequest(
            content_type="lecture",
            topic="AI basics",
            user_prompt="Generate a short lecture",
            generation_options={"include_images": False, "include_mindmap": False, "max_section_count": 1},
        )
    )

    service.run_task(created.task_id)

    task = repository.get_task(created.task_id)
    metrics = repository.list_metrics(created.task_id)
    assert task is not None
    assert task.status == TaskStatus.completed
    assert metrics
    assert any(metric.node == "finalize_task" for metric in metrics)
    assert all(metric.task_id == created.task_id for metric in metrics)
    assert all(metric.duration_ms is None or metric.duration_ms >= 0 for metric in metrics)
