from fastapi.testclient import TestClient

from app.api.content_generation import task_service
from app.main import app


client = TestClient(app)


def wait_for_completed_task(task_id: str) -> dict[str, object]:
    response = client.get(f"/api/content-generation/tasks/{task_id}")
    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "completed"
    return task


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
    assert created["status"] in {"queued", "running"}
    assert created["content_type"] == "lecture"
    assert created["export_files"] == []

    task_id = created["task_id"]
    task = wait_for_completed_task(task_id)
    assert task["preview_url"] == f"/api/content-generation/tasks/{task_id}/preview"
    assert task["progress"]["percent"] == 100

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
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)
    preview = client.get(f"/api/content-generation/tasks/{task_id}/preview").json()
    image_block = next(block for block in preview["render_model"]["sections"][0]["render_blocks"] if block["type"] == "image")
    asset_id = image_block["asset_url"].split("/api/assets/", 1)[1].split("/", 1)[0]

    response = client.get(f"/api/assets/{asset_id}")

    assert response.status_code == 200
    asset = response.json()
    assert asset["asset_id"] == asset_id
    assert asset["kind"] == "image"
    assert asset["url"] == f"/api/assets/{asset_id}/download"


def test_social_post_task_lifecycle_exposes_html_preview_and_export() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "social_post",
            "topic": "Direct workflow for social posts",
            "user_prompt": "Generate a WeChat article about direct workflow architecture.",
            "knowledge_base_ids": ["kb_ai_basic"],
            "generation_options": {
                "language": "zh-CN",
                "include_images": True,
                "citation_policy": "light",
            },
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    task = wait_for_completed_task(task_id)
    assert task["content_type"] == "social_post"
    assert task["preview_url"] == f"/api/content-generation/tasks/{task_id}/preview"

    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["content_type"] == "social_post"
    assert preview["render_model"]["render_type"] == "social_post"
    assert preview["render_model"]["html"]
    assert preview["render_model"]["article_json"]["template"]

    export_response = client.post(
        f"/api/content-generation/tasks/{task_id}/export",
        json={"export_type": "html"},
    )
    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["export_type"] == "html"
    assert exported["status"] == "success"

    unsupported_response = client.post(
        f"/api/content-generation/tasks/{task_id}/export",
        json={"export_type": "slide_json"},
    )
    assert unsupported_response.status_code == 200
    unsupported = unsupported_response.json()
    assert unsupported["export_type"] == "slide_json"
    assert unsupported["status"] == "failed"


def test_content_generation_api_exposes_artifacts_references_metrics_and_platform_context() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        headers={
            "X-Platform-Log-Id": "platform_log_001",
            "X-Platform-User-Id": "platform_user_001",
            "X-Platform-Session-Id": "platform_session_001",
        },
        json={
            "content_type": "lecture",
            "topic": "Artifact API",
            "user_prompt": "Generate a short lecture with references",
            "knowledge_base_ids": ["kb_ai_basic"],
            "generation_options": {"include_images": False, "include_mindmap": False, "max_section_count": 1},
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)

    task_record = task_service.repository.get_task(task_id)
    assert task_record is not None
    assert task_record.platform_log_id == "platform_log_001"
    assert task_record.platform_user_id == "platform_user_001"
    assert task_record.platform_session_id == "platform_session_001"

    artifacts_response = client.get(f"/api/content-generation/tasks/{task_id}/artifacts")
    assert artifacts_response.status_code == 200
    artifacts_payload = artifacts_response.json()
    assert artifacts_payload["task_id"] == task_id
    artifact_types = {artifact["artifact_type"] for artifact in artifacts_payload["artifacts"]}
    assert {"outline", "content_spec", "final_render"}.issubset(artifact_types)

    outline_artifact = next(artifact for artifact in artifacts_payload["artifacts"] if artifact["artifact_type"] == "outline")
    detail_response = client.get(f"/api/content-generation/tasks/{task_id}/artifacts/{outline_artifact['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["artifact"]["payload"]["title"] == "Artifact API"

    outline_response = client.get(f"/api/content-generation/tasks/{task_id}/outline")
    assert outline_response.status_code == 200
    assert outline_response.json()["artifact"]["artifact_type"] == "outline"

    references_response = client.get(f"/api/content-generation/tasks/{task_id}/references")
    assert references_response.status_code == 200
    references_payload = references_response.json()
    assert references_payload["task_id"] == task_id
    assert references_payload["unit_id"] is None
    assert references_payload["content_type"] == "lecture"
    assert references_payload["title"] == "Artifact API"
    assert references_payload["chunks"]
    assert {"chunk_id", "path", "title", "text", "rank", "score"}.issubset(references_payload["chunks"][0])
    assert references_payload["chunks"][0]["path"]
    assert references_payload["chunks"][0]["title"]
    assert references_payload["chunks"][0]["text"]

    units_response = client.get(f"/api/content-generation/tasks/{task_id}/units")
    assert units_response.status_code == 200
    unit_id = units_response.json()["units"][0]["unit_id"]
    unit_references_response = client.get(f"/api/content-generation/tasks/{task_id}/units/{unit_id}/references")
    assert unit_references_response.status_code == 200
    unit_references_payload = unit_references_response.json()
    assert unit_references_payload["task_id"] == task_id
    assert unit_references_payload["unit_id"] == unit_id
    assert unit_references_payload["content_type"] == "lecture"
    assert unit_references_payload["title"]
    assert unit_references_payload["chunks"]
    assert {"chunk_id", "path", "title", "text", "rank", "score"}.issubset(unit_references_payload["chunks"][0])

    metrics_response = client.get(f"/api/content-generation/tasks/{task_id}/metrics")
    assert metrics_response.status_code == 200
    metrics_payload = metrics_response.json()
    assert metrics_payload["task_id"] == task_id
    assert metrics_payload["metrics"] == []

    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    assert preview_response.status_code == 200
    assert preview_response.json()["render_model"]["render_type"] == "lecture_page"
