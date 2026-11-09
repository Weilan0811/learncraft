from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.request import ContentGenerationRequest
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService


def make_service(tmp_path: Path) -> PersistentTaskService:
    repository = SQLModelTaskRepository(
        database_url=f"sqlite:///{tmp_path / 'task_list.db'}",
        echo=False,
        create_tables=True,
    )
    return PersistentTaskService(repository=repository)


def create_task(
    service: PersistentTaskService,
    *,
    content_type: str,
    topic: str,
    status: str,
    created_at: datetime,
    failed_resources: int = 0,
) -> str:
    task = service.create_task(ContentGenerationRequest(content_type=content_type, topic=topic, user_prompt="Generate"))
    service.repository.update_task(
        task.task_id,
        status=status,
        created_at=created_at,
        progress={
            "stage": status,
            "percent": 100,
            "resource_summary": {"total": failed_resources, "failed": failed_resources, "retrying": 0},
        },
    )
    return task.task_id


def test_repository_lists_tasks_newest_first_with_pagination(tmp_path) -> None:
    service = make_service(tmp_path)
    base = datetime(2026, 11, 1, tzinfo=UTC)
    ids = [
        create_task(
            service,
            content_type="lecture",
            topic=f"Lecture {index}",
            status="completed",
            created_at=base + timedelta(minutes=index),
            failed_resources=index,
        )
        for index in range(5)
    ]

    rows, total = service.repository.list_tasks(page=1, page_size=2)
    assert total == 5
    assert [row.task_id for row in rows] == [ids[4], ids[3]]

    second_page, _ = service.repository.list_tasks(page=2, page_size=2)
    assert [row.task_id for row in second_page] == [ids[2], ids[1]]

    filtered, filtered_total = service.repository.list_tasks(content_type="social_post")
    assert filtered == []
    assert filtered_total == 0


def test_service_list_exposes_failed_resource_count(tmp_path) -> None:
    service = make_service(tmp_path)
    create_task(
        service,
        content_type="lecture",
        topic="With failures",
        status="completed",
        created_at=datetime(2026, 11, 2, tzinfo=UTC),
        failed_resources=2,
    )
    create_task(
        service,
        content_type="lecture",
        topic="Clean",
        status="interrupted",
        created_at=datetime(2026, 11, 1, tzinfo=UTC),
    )

    response = service.list_tasks(page=1, page_size=10)

    assert response.total == 2
    assert response.items[0].topic == "With failures"
    assert response.items[0].failed_resource_count == 2
    assert response.items[1].status == "interrupted"
    assert response.items[1].failed_resource_count == 0


def test_task_list_endpoint_supports_filters_and_validation(tmp_path, monkeypatch) -> None:
    service = make_service(tmp_path)
    monkeypatch.setattr("app.api.content_generation.task_service", service)
    lecture_id = create_task(
        service,
        content_type="lecture",
        topic="Lecture task",
        status="completed",
        created_at=datetime(2026, 11, 3, tzinfo=UTC),
        failed_resources=1,
    )
    create_task(
        service,
        content_type="slide_deck",
        topic="Slide task",
        status="failed",
        created_at=datetime(2026, 11, 4, tzinfo=UTC),
    )
    client = TestClient(app)

    response = client.get(
        "/api/content-generation/tasks",
        params={"content_type": "lecture", "status": "completed", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert payload["items"][0]["task_id"] == lecture_id
    assert payload["items"][0]["content_type"] == "lecture"
    assert payload["items"][0]["status"] == "completed"
    assert payload["items"][0]["failed_resource_count"] == 1

    invalid_page = client.get("/api/content-generation/tasks", params={"page": 0})
    assert invalid_page.status_code == 422
    invalid_status = client.get("/api/content-generation/tasks", params={"status": "unknown"})
    assert invalid_status.status_code == 422

    all_tasks = client.get("/api/content-generation/tasks", params={"page_size": 10})
    assert [item["topic"] for item in all_tasks.json()["items"]] == ["Slide task", "Lecture task"]
