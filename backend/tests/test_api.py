from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "content-generator-agent"}


def test_content_generation_task_lifecycle_exposes_stub_result() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "lecture",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份适合本科一年级学生学习的多模态讲义",
            "knowledge_base_ids": ["kb_ai_basic"],
            "generation_options": {
                "language": "zh-CN",
                "difficulty": "introductory",
                "include_images": True,
                "include_charts": True,
                "include_mindmap": True,
            },
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "completed"
    assert created["content_type"] == "lecture"
    assert created["export_files"] == []

    task_id = created["task_id"]
    status_response = client.get(f"/api/content-generation/tasks/{task_id}")
    assert status_response.status_code == 200
    assert status_response.json()["preview_url"] == f"/api/content-generation/tasks/{task_id}/preview"

    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["content_type"] == "lecture"
    assert preview["render_model"]["render_type"] == "lecture_page"

    export_response = client.post(
        f"/api/content-generation/tasks/{task_id}/export",
        json={"export_type": "pdf"},
    )
    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["export_type"] == "pdf"
    assert exported["status"] == "success"
    assert exported["file_url"].startswith("/api/assets/")
    assert exported["file_url"].endswith("/download")

    status_after_export = client.get(f"/api/content-generation/tasks/{task_id}")
    assert status_after_export.status_code == 200
    assert status_after_export.json()["export_files"] == [{"type": "pdf", "url": exported["file_url"]}]

    download_response = client.get(exported["file_url"])
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")
    assert download_response.content.startswith(b"%PDF-")


def test_asset_endpoint_returns_local_asset_metadata() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "lecture",
            "topic": "人工智能基础导论",
            "user_prompt": "生成一份讲义",
            "generation_options": {"include_images": True},
        },
    )
    assert create_response.status_code == 201

    response = client.get("/api/assets/img_stub")

    assert response.status_code == 200
    asset = response.json()
    assert asset["asset_id"] == "img_stub"
    assert asset["kind"] == "image"
    assert asset["url"] == "/api/assets/img_stub/download"
