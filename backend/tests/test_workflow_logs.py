import json

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
    assert task.logs
    assert any(entry["event"] == "task_started" for entry in task.logs)
    assert any(entry["event"] == "node_completed" and entry["node"] == "finalize_task" for entry in task.logs)

    log_path = task_log_file_path(created.task_id)
    assert log_path.exists()
    file_entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(entry["task_id"] == created.task_id for entry in file_entries)
    assert any(entry["event"] == "task_completed" for entry in file_entries)
    get_settings.cache_clear()
