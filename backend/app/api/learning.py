"""
P0 Learning Session and Event API routes.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.learning import (
    CreateSessionRequest,
    EventResponse,
    SessionResponse,
    SessionStateResponse,
    SubmitEventRequest,
)
from app.services.learning_service import get_learning_service

router = APIRouter()


@router.post("/interactive-lessons/{lesson_id}/sessions", response_model=SessionResponse)
def create_learning_session(lesson_id: str, request: CreateSessionRequest = CreateSessionRequest()):
    """Create a new learning session for an interactive HTML lesson."""
    service = get_learning_service()
    return service.create_session(lesson_id, request)


@router.post(
    "/interactive-lessons/{lesson_id}/sessions/{session_id}/events",
    response_model=EventResponse,
)
def submit_learning_event(lesson_id: str, session_id: str, request: SubmitEventRequest):
    """Submit a learning event (answer, hint request, etc.) during an interactive session."""
    service = get_learning_service()
    try:
        return service.submit_event(lesson_id, session_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/interactive-lessons/{lesson_id}/sessions/{session_id}/state",
    response_model=SessionStateResponse,
)
def get_learning_session_state(lesson_id: str, session_id: str):
    """Get the current state of a learning session."""
    service = get_learning_service()
    try:
        return service.get_session_state(lesson_id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
