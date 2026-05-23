"""
P0 Learning Session and Event services (in-memory storage).
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.learning import (
    CreateSessionRequest,
    EventFeedback,
    EventResponse,
    LearningEventPayload,
    SessionResponse,
    SessionStateResponse,
    SubmitEventRequest,
)


class InMemoryLearningService:
    """P0 in-memory storage for learning sessions and events."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}

    def create_session(self, lesson_id: str, _request: CreateSessionRequest) -> SessionResponse:
        session_id = f"session_{uuid4().hex[:12]}"
        session = {
            "session_id": session_id,
            "lesson_id": lesson_id,
            "state": {},
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._sessions[session_id] = session
        self._events[session_id] = []
        return SessionResponse(
            session_id=session_id,
            lesson_id=lesson_id,
            state={},
        )

    def submit_event(self, lesson_id: str, session_id: str, request: SubmitEventRequest) -> EventResponse:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        event_id = f"event_{uuid4().hex[:12]}"
        event = {
            "event_id": event_id,
            "lesson_id": lesson_id,
            "session_id": session_id,
            "section_id": request.section_id,
            "block_id": request.block_id or request.interaction_id or request.section_id,
            "interaction_id": request.interaction_id,
            "event_type": request.event_type,
            "payload": request.payload.model_dump(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._events[session_id].append(event)

        return EventResponse(
            event_id=event_id,
            feedback=EventFeedback(
                message="你的回答已记录，请继续学习下一部分。",
                tone="encouraging",
            ),
            event_saved=True,
        )

    def get_session_state(self, lesson_id: str, session_id: str) -> SessionStateResponse:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        events = self._events.get(session_id, [])
        summary = self._build_interaction_summary(events)

        return SessionStateResponse(
            session_id=session_id,
            lesson_id=lesson_id,
            total_events=len(events),
            interaction_summary=summary,
        )

    def list_events(self, lesson_id: str, session_id: str) -> list[dict]:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        session = self._sessions[session_id]
        if session["lesson_id"] != lesson_id:
            raise ValueError(f"Session {session_id} does not belong to lesson {lesson_id}")
        return [dict(event) for event in self._events.get(session_id, [])]

    def _build_interaction_summary(self, events: list[dict]) -> dict:
        answered = sum(1 for e in events if e["event_type"] in {
            "single_choice_answered", "multiple_choice_answered",
            "short_answer_submitted", "scenario_discussion_submitted", "drag_match_submitted",
            "sequence_submitted",
        })
        help_requested = sum(1 for e in events if e["event_type"] in {
            "hint_requested", "confused_clicked",
        })
        return {
            "total_answered": answered,
            "help_requested_count": help_requested,
            "total_events": len(events),
        }


_learning_service: InMemoryLearningService | None = None


def get_learning_service() -> InMemoryLearningService:
    global _learning_service
    if _learning_service is None:
        _learning_service = InMemoryLearningService()
    return _learning_service
