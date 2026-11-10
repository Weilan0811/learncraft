from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
LESSON_ID = "lesson_learning_api_test"


def test_learning_summary_and_adaptive_brief_flow() -> None:
    session = client.post(f"/api/interactive-lessons/{LESSON_ID}/sessions", json={})
    assert session.status_code == 200
    session_id = session.json()["session_id"]

    empty = client.get(f"/api/interactive-lessons/{LESSON_ID}/sessions/{session_id}/summary")
    assert empty.status_code == 200
    assert empty.json()["total_answered"] == 0

    no_evidence = client.post(
        f"/api/interactive-lessons/{LESSON_ID}/sessions/{session_id}/adaptive-brief",
        json={},
    )
    assert no_evidence.status_code == 409

    event = client.post(
        f"/api/interactive-lessons/{LESSON_ID}/sessions/{session_id}/events",
        json={
            "section_id": "s1",
            "interaction_id": "i1",
            "event_type": "single_choice_answered",
            "payload": {"selected_option_ids": ["a"], "is_correct": True},
        },
    )
    assert event.status_code == 200

    summary = client.get(f"/api/interactive-lessons/{LESSON_ID}/sessions/{session_id}/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_answered"] == 1
    assert payload["accuracy"] == 1.0
    assert payload["completion_rate"] == 1.0

    brief = client.post(
        f"/api/interactive-lessons/{LESSON_ID}/sessions/{session_id}/adaptive-brief",
        json={},
    )
    assert brief.status_code == 200
    brief_payload = brief.json()
    assert brief_payload["suggested_difficulty"] == "advanced"
    assert brief_payload["evidence"]["total_answered"] == 1
    assert LESSON_ID in brief_payload["topic_suggestion"]


def test_learning_summary_rejects_unknown_session() -> None:
    response = client.get(f"/api/interactive-lessons/{LESSON_ID}/sessions/session_missing/summary")
    assert response.status_code == 404
