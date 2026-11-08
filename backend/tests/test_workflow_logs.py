import json
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import task_log_file_path
from app.schemas.request import ContentGenerationRequest
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService

from tests.test_task_persistence import sqlite_url


def test_task_service_persists_structured_logs_and_writes_jsonl_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    get_settings.cache_clear()
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
    assert task is not None
    assert not hasattr(task, "logs")

    log_path = task_log_file_path(created.task_id)
    assert log_path.exists()
    file_entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(entry["task_id"] == created.task_id for entry in file_entries)
    assert any(entry["event"] == "task_started" for entry in file_entries)
    assert any(entry["event"] == "node_completed" and entry["node"] == "finalize_task" for entry in file_entries)
    assert any(entry["event"] == "task_completed" for entry in file_entries)
    get_settings.cache_clear()


def test_task_service_writes_debug_artifacts_for_workflow_steps(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", str(tmp_path / "debug_workflow"))
    get_settings.cache_clear()
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False)
    service = PersistentTaskService(repository=repository)
    created = service.create_task(
        ContentGenerationRequest(
            content_type="social_post",
            topic="Direct workflow",
            user_prompt="Generate a WeChat article",
            generation_options={"include_images": True},
        )
    )

    service.run_task(created.task_id)

    debug_dir = Path(tmp_path / "debug_workflow" / created.task_id)
    trace_path = debug_dir / "trace.json"
    content_spec_path = debug_dir / "content_spec.json"
    render_model_path = debug_dir / "render_model.json"

    assert trace_path.exists()
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert any(step["node"] == "generate_direct_content" for step in trace)
    assert all((debug_dir / "steps" / f"{step['step']:02d}_{step['node']}.json").exists() for step in trace)
    assert content_spec_path.exists()
    assert render_model_path.exists()

    log_path = task_log_file_path(created.task_id)
    file_entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(entry["detail"].get("debug_artifact_path") for entry in file_entries if entry["event"] == "node_completed")
    get_settings.cache_clear()


def test_empty_retrieval_is_visible_in_workflow_logs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", str(tmp_path / "logs"))
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", str(tmp_path / "debug_workflow"))
    get_settings.cache_clear()

    from app.workflows.nodes.retriever_node import retrieve_for_planning
    from app.schemas.state import ContentGenerationState

    class EmptyRAG:
        last_diagnostics = {"status": "failed", "query_preview": "Agent workflow", "error_message": "boom"}

        def retrieve(self, request, stage: str, section_hint: str | None = None):
            return []

    monkeypatch.setattr("app.workflows.nodes.retriever_node.get_rag_service", lambda: EmptyRAG())

    state = ContentGenerationState(
        request_id="task_empty_retrieval",
        content_type="social_post",
        topic="Agent workflow",
        user_prompt="Generate a WeChat article",
        knowledge_base_ids=["kb_ai_basic"],
    )

    result = retrieve_for_planning(state)

    assert result["retrieved_chunks"] == []
    assert result["workflow_errors"]
    assert result["workflow_errors"][0]["code"] == "empty_retrieval"
    assert "query_preview" in result["workflow_errors"][0]["detail"]
    get_settings.cache_clear()
