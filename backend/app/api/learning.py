"""
P0 Learning Session and Event API routes.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.learning import (
    AdaptiveBriefRequest,
    AdaptiveBriefResponse,
    CreateSessionRequest,
    EventResponse,
    SessionResponse,
    SessionStateResponse,
    SessionSummaryResponse,
    SubmitEventRequest,
)
from app.services.adaptive_brief_service import (
    AdaptiveBriefService,
    NoLearningEvidenceError,
    load_lesson_context,
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


@router.get(
    "/interactive-lessons/{lesson_id}/sessions/{session_id}/summary",
    response_model=SessionSummaryResponse,
)
def get_learning_session_summary(lesson_id: str, session_id: str):
    """Summarize answers, weak concepts and review sections for a session."""
    service = get_learning_service()
    try:
        context = load_lesson_context(lesson_id)
        return service.build_summary(
            lesson_id,
            session_id,
            section_titles=context.section_titles,
            concept_map=context.concept_map,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/interactive-lessons/{lesson_id}/sessions/{session_id}/adaptive-brief",
    response_model=AdaptiveBriefResponse,
)
def create_adaptive_brief(
    lesson_id: str,
    session_id: str,
    request: AdaptiveBriefRequest = AdaptiveBriefRequest(),
):
    """Build a rule-based brief for regenerating the lesson around weak points."""
    service = get_learning_service()
    try:
        return AdaptiveBriefService(service).build(lesson_id, session_id, request.difficulty)
    except NoLearningEvidenceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
