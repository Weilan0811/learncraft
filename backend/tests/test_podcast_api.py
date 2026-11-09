from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def wait_for_completed_task(task_id: str) -> dict[str, object]:
    response = client.get(f"/api/content-generation/tasks/{task_id}")
    assert response.status_code == 200
    task = response.json()
    assert task["status"] == "completed"
    return task


def test_podcast_task_lifecycle_exposes_script_audio_preview_and_exports() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "podcast_script",
            "topic": "Direct workflow for podcasts",
            "user_prompt": "Generate a Chinese podcast dialogue about direct workflow architecture.",
            "knowledge_base_ids": ["kb_ai_basic"],
            "generation_options": {
                "language": "zh-CN",
                "style": "chinese_podcast_dialogue",
            },
        },
    )

    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    task = wait_for_completed_task(task_id)
    assert task["content_type"] == "podcast_script"
    assert task["preview_url"] == f"/api/content-generation/tasks/{task_id}/preview"

    preview_response = client.get(f"/api/content-generation/tasks/{task_id}/preview")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["content_type"] == "podcast_script"
    assert preview["render_model"]["render_type"] == "podcast_script"
    assert "Person1" in preview["render_model"]["script_text"]
    assert preview["render_model"]["segments"][0]["voice"] == "Ethan"
    assert preview["render_model"]["segments"][1]["voice"] == "Cherry"
    assert preview["render_model"]["audio_manifest_url"].startswith("/api/assets/")

    events_response = client.get(f"/api/content-generation/tasks/{task_id}/events")
    assert events_response.status_code == 200
    event_types = [event["type"] for event in events_response.json()["events"]]
    assert event_types.count("audio_segment_ready") == len(preview["render_model"]["segments"])

    markdown_response = client.post(f"/api/content-generation/tasks/{task_id}/export", json={"export_type": "markdown"})
    assert markdown_response.status_code == 200
    markdown = markdown_response.json()
    assert markdown["status"] == "success"
    assert markdown["file_url"].endswith("/download")

    audio_response = client.post(f"/api/content-generation/tasks/{task_id}/export", json={"export_type": "audio"})
    assert audio_response.status_code == 200
    audio = audio_response.json()
    assert audio["status"] == "success"
    assert preview["render_model"]["final_audio_url"].startswith("/api/assets/")
    assert audio["file_url"] == preview["render_model"]["final_audio_url"]
