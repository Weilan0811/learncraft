from pathlib import Path

from app.core.config import Settings
from app.core.task import TaskStatus
from app.schemas.request import ContentGenerationRequest
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService
from app.workflows.nodes.helpers import build_progress, ensure_monotonic_progress


def sqlite_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path / 'tasks.db'}"


def test_settings_build_platform_mysql_database_url_from_db_env(monkeypatch) -> None:
    monkeypatch.delenv("CONTENT_GENERATOR_DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "mysql.internal")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_USERNAME", "future")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("DB_DATABASE", "future_learning")

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL == "mysql+pymysql://future:secret@mysql.internal:3307/future_learning"


def test_task_service_persists_render_model_across_service_instances(tmp_path) -> None:
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False)
    service = PersistentTaskService(repository=repository)
    request = ContentGenerationRequest(
        content_type="lecture",
        topic="AI basics",
        user_prompt="Generate a short lecture",
        generation_options={"include_images": True, "include_mindmap": True},
    )

    created = service.create_task(request)
    assert created.status == TaskStatus.queued

    service.run_task(created.task_id)

    restarted_service = PersistentTaskService(repository=SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False))
    task = restarted_service.get_task(created.task_id)
    preview = restarted_service.get_preview(created.task_id)

    assert task is not None
    assert task.status == TaskStatus.completed
    assert task.progress["percent"] == 100
    assert preview is not None
    assert preview.render_model.render_type == "lecture_page"
    assert preview.render_model.title == "AI basics"


def test_task_persistence_tracks_distinct_image_assets_for_each_task(tmp_path) -> None:
    repository = SQLModelTaskRepository(database_url=sqlite_url(tmp_path), echo=False)
    service = PersistentTaskService(repository=repository)
    first = service.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Task one", user_prompt="Generate one", generation_options={"include_images": True})
    )
    second = service.create_task(
        ContentGenerationRequest(content_type="lecture", topic="Task two", user_prompt="Generate two", generation_options={"include_images": True})
    )

    service.run_task(first.task_id)
    service.run_task(second.task_id)

    first_record = repository.get_task(first.task_id)
    second_record = repository.get_task(second.task_id)
    first_preview = service.get_preview(first.task_id)
    second_preview = service.get_preview(second.task_id)
    assert first_record is not None
    assert second_record is not None
    assert first_preview is not None
    assert second_preview is not None
    first_urls = [block.asset_url for section in first_preview.render_model.sections for block in section.render_blocks if block.type == "image"]
    second_urls = [block.asset_url for section in second_preview.render_model.sections for block in section.render_blocks if block.type == "image"]
    assert first_urls
    assert second_urls
    assert first_urls != second_urls
    assert all("img_stub" not in url for url in first_urls)


def test_progress_percent_is_monotonic_across_looping_nodes() -> None:
    previous = build_progress(
        stage="unit_completed",
        current_node="merge_unit_result",
        current_unit_id="unit_001",
        completed_units=1,
        total_units=2,
    )
    next_loop = build_progress(
        stage="retrieving_unit",
        current_node="retrieve_for_unit",
        current_unit_id="unit_002",
        completed_units=1,
        total_units=2,
    )

    stable = ensure_monotonic_progress(previous, next_loop)

    assert next_loop["current_node"] == "retrieve_for_unit"
    assert stable["percent"] >= previous["percent"]
    assert stable["stage"] == "retrieving_unit"
