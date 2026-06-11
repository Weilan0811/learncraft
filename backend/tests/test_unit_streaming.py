import pytest

from app.core.config import get_settings
from app.schemas.request import ContentGenerationRequest, GenerationOptions
from app.api.content_generation import task_service
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService
from app.workflows.content_generation_graph import run_content_generation

from tests.test_api import client, wait_for_completed_task
from tests.test_task_persistence import sqlite_url


def test_workflow_publishes_unit_render_snapshots_for_lecture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()

    state = run_content_generation(
        ContentGenerationRequest(
            content_type="lecture",
            topic="AI basics",
            user_prompt="Generate a lecture",
            generation_options=GenerationOptions(include_images=False, include_mindmap=False, max_section_count=2),
        )
    )

    assert state.status == "completed"
    assert state.render_units
    assert state.partial_render_model is not None
    assert state.partial_render_model.render_type == "lecture_page"
    assert len(state.partial_render_model.sections) == len(state.completed_unit_ids)
    assert any(event.type == "unit_render_ready" for event in state.stream_events)
    assert all(snapshot.status == "rendered" for snapshot in state.render_units.values())
    get_settings.cache_clear()


def test_workflow_publishes_unit_render_snapshots_for_slide_deck(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
    get_settings.cache_clear()

    state = run_content_generation(
        ContentGenerationRequest(
            content_type="slide_deck",
            topic="AI basics",
            user_prompt="Generate a deck",
            generation_options=GenerationOptions(include_images=False, include_mindmap=False, max_slide_count=2),
        )
    )

    assert state.status == "completed"
    assert state.render_units
    assert state.partial_render_model is not None
    assert state.partial_render_model.render_type == "slide_deck"
    assert len(state.partial_render_model.pages) == len(state.completed_unit_ids)
    assert any(event.type == "unit_render_ready" for event in state.stream_events)
    get_settings.cache_clear()


def test_repository_persists_partial_streaming_state(tmp_path) -> None:
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

    record = repository.get_task(created.task_id)
    assert record is not None
    assert record.outline is not None
    assert record.unit_results
    assert record.render_units
    assert record.partial_render_model is not None
    assert record.stream_events


def test_api_exposes_events_partial_preview_and_unit_previews() -> None:
    create_response = client.post(
        "/api/content-generation/tasks",
        json={
            "content_type": "slide_deck",
            "topic": "AI basics",
            "user_prompt": "Generate a deck",
            "generation_options": {"include_images": False, "include_mindmap": False, "max_slide_count": 1},
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    wait_for_completed_task(task_id)

    events_response = client.get(f"/api/content-generation/tasks/{task_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    assert any(event["type"] == "unit_render_ready" for event in events)

    partial_response = client.get(f"/api/content-generation/tasks/{task_id}/preview/partial")
    assert partial_response.status_code == 200
    partial = partial_response.json()
    assert partial["content_type"] == "slide_deck"
    assert partial["render_model"]["render_type"] == "slide_deck"
    assert partial["is_partial"] is True

    units_response = client.get(f"/api/content-generation/tasks/{task_id}/units")
    assert units_response.status_code == 200
    units = units_response.json()["units"]
    assert len(units) == 1
    unit_id = units[0]["unit_id"]

    unit_preview_response = client.get(f"/api/content-generation/tasks/{task_id}/units/{unit_id}/preview")
    assert unit_preview_response.status_code == 200
    assert unit_preview_response.json()["unit_id"] == unit_id


def test_api_exposes_plain_text_for_unit_chunks() -> None:
    created = task_service.create_task(
        ContentGenerationRequest(
            content_type="interactive_html",
            topic="Prompt understanding",
            user_prompt="Generate an interactive lesson",
            generation_options={"include_images": False, "include_mindmap": False, "max_section_count": 1},
        )
    )
    task_service.repository.update_task(
        created.task_id,
        render_units={
            "unit-01-intro": {
                "unit_id": "unit-01-intro",
                "order": 1,
                "content_type": "interactive_html",
                "status": "rendered",
                "render_fragment": {
                    "section_id": "unit-01-intro",
                    "title": "Prompt journey",
                    "learning_goal": "Understand how prompts become model input",
                    "style_scope_id": "ih-scope-unit-01",
                    "html_fragment": (
                        '<section id="unit-01-intro">'
                        '<article data-block-id="intro-block"><h2>Prompt <em>journey</em></h2><p>Hello&nbsp;AI.</p></article>'
                        '<article data-block-id="practice-block"><h3>Practice</h3><p>Choose &amp; explain.</p></article>'
                        "</section>"
                    ),
                    "css_fragment": "",
                    "block_manifest": [
                        {
                            "block_id": "intro-block",
                            "type": "intro",
                            "title": "Prompt journey",
                            "teaching_role": "set_context",
                            "interaction_ids": [],
                        },
                        {
                            "block_id": "practice-block",
                            "type": "practice",
                            "title": "Practice",
                            "teaching_role": "check_understanding",
                            "interaction_ids": [],
                        },
                    ],
                    "interaction_manifest": [],
                    "render_notes": {},
                },
                "updated_at": "2026-06-11T00:00:00Z",
                "errors": [],
            }
        },
    )

    response = client.get(f"/api/content-generation/tasks/{created.task_id}/units/unit-01-intro/text")

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == created.task_id
    assert payload["unit_id"] == "unit-01-intro"
    assert payload["content_type"] == "interactive_html"
    assert payload["title"] == "Prompt journey"
    assert payload["full_text"] == "Prompt journey Hello AI. Practice Choose & explain."
    assert payload["chunks"] == [
        {"chunk_id": "chunk-01", "text": "Prompt journey Hello AI."},
        {"chunk_id": "chunk-02", "text": "Practice Choose & explain."},
    ]
