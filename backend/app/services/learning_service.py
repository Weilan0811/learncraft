"""
Learning session and event services.

``LearningService`` persists sessions/events through
``SQLModelLearningRepository`` and derives the learning summary used by the
adaptive brief. ``InMemoryLearningService`` remains for tests that only need
the event contract (for example the offline handout exporter).
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.lesson import normalize_lesson_id
from app.schemas.learning import (
    CreateSessionRequest,
    EventFeedback,
    EventResponse,
    SectionProgress,
    SessionResponse,
    SessionStateResponse,
    SessionSummaryResponse,
    SubmitEventRequest,
    WeakConcept,
)
from app.services.learning_repository import SQLModelLearningRepository


ANSWERED_EVENT_TYPES = frozenset(
    {
        "single_choice_answered",
        "multiple_choice_answered",
        "short_answer_submitted",
        "scenario_discussion_submitted",
        "drag_match_submitted",
        "sequence_submitted",
        "socratic_round_answered",
        "scenario_choice_selected",
    }
)
HELP_EVENT_TYPES = frozenset({"hint_requested", "confused_clicked"})
WEAK_SECTION_ACCURACY = 0.6
PASSING_HEURISTIC_SCORE = 60


def build_interaction_summary(events: list[dict]) -> dict:
    answered = sum(1 for event in events if event["event_type"] in ANSWERED_EVENT_TYPES)
    help_requested = sum(1 for event in events if event["event_type"] in HELP_EVENT_TYPES)
    return {
        "total_answered": answered,
        "help_requested_count": help_requested,
        "total_events": len(events),
    }


def _event_correctness(payload: dict) -> tuple[bool | None, bool]:
    """Return (is_correct, is_scored)."""
    is_correct = payload.get("is_correct")
    if isinstance(is_correct, bool):
        return is_correct, True
    score = payload.get("heuristic_score")
    if isinstance(score, int):
        return score >= PASSING_HEURISTIC_SCORE, True
    return None, False


class LearningService:
    """Persistent learning sessions and events."""

    def __init__(self, repository: SQLModelLearningRepository) -> None:
        self.repository = repository

    def create_session(self, lesson_id: str, _request: CreateSessionRequest) -> SessionResponse:
        lesson_id = normalize_lesson_id(lesson_id)
        session = self.repository.create_session(lesson_id)
        return SessionResponse(
            session_id=session["session_id"],
            lesson_id=lesson_id,
            state=session.get("state") or {},
        )

    def submit_event(self, lesson_id: str, session_id: str, request: SubmitEventRequest) -> EventResponse:
        lesson_id = normalize_lesson_id(lesson_id)
        self._require_session(lesson_id, session_id)
        event = self.repository.add_event(
            session_id=session_id,
            lesson_id=lesson_id,
            section_id=request.section_id,
            block_id=request.block_id or request.interaction_id or request.section_id,
            interaction_id=request.interaction_id,
            event_type=request.event_type,
            payload=request.payload.model_dump(),
        )
        return EventResponse(
            event_id=event["event_id"],
            feedback=EventFeedback(
                message="你的回答已记录，请继续学习下一部分。",
                tone="encouraging",
            ),
            event_saved=True,
        )

    def get_session_state(self, lesson_id: str, session_id: str) -> SessionStateResponse:
        lesson_id = normalize_lesson_id(lesson_id)
        self._require_session(lesson_id, session_id)
        events = self.repository.list_events(session_id)
        return SessionStateResponse(
            session_id=session_id,
            lesson_id=lesson_id,
            total_events=len(events),
            interaction_summary=build_interaction_summary(events),
        )

    def list_events(self, lesson_id: str, session_id: str) -> list[dict]:
        self._require_session(lesson_id, session_id)
        return self.repository.list_events(session_id)

    def build_summary(
        self,
        lesson_id: str,
        session_id: str,
        *,
        section_titles: dict[str, str] | None = None,
        concept_map: dict[str, list[str]] | None = None,
    ) -> SessionSummaryResponse:
        lesson_id = normalize_lesson_id(lesson_id)
        self._require_session(lesson_id, session_id)
        events = self.repository.list_events(session_id)
        titles = dict(section_titles or {})
        concepts_by_interaction = dict(concept_map or {})

        sections: dict[str, dict] = {
            section_id: _empty_section(section_id, title) for section_id, title in titles.items()
        }
        concept_scores: dict[str, dict] = {}

        total_answered = 0
        total_correct = 0
        total_scored = 0
        help_requested = 0
        total_time = 0

        for event in events:
            section_id = event["section_id"]
            section = sections.setdefault(section_id, _empty_section(section_id, titles.get(section_id)))
            payload = event.get("payload") or {}
            time_spent = payload.get("time_spent_seconds")
            if isinstance(time_spent, int) and time_spent > 0:
                section["time_spent_seconds"] += time_spent
                total_time += time_spent

            interaction_id = event.get("interaction_id")
            concept_names = concepts_by_interaction.get(interaction_id, []) if interaction_id else []

            if event["event_type"] in ANSWERED_EVENT_TYPES:
                section["answered_count"] += 1
                total_answered += 1
                is_correct, is_scored = _event_correctness(payload)
                if is_scored:
                    section["scored_count"] += 1
                    total_scored += 1
                    if is_correct:
                        section["correct_count"] += 1
                        total_correct += 1
                    else:
                        _add_concept_scores(concept_scores, concept_names, section_id, points=2)
            elif event["event_type"] in HELP_EVENT_TYPES:
                section["help_requested_count"] += 1
                help_requested += 1
                _add_concept_scores(concept_scores, concept_names, section_id, points=1)

        section_progress = [_finalize_section(section) for section in sections.values()]
        section_progress.sort(key=lambda item: item.section_id)
        for item in section_progress:
            item.is_weak = (item.scored_count > 0 and (item.accuracy or 0.0) < WEAK_SECTION_ACCURACY) or (
                item.help_requested_count > 0
            )

        answered_sections = sum(1 for item in section_progress if item.answered_count > 0)
        total_sections = max(len(titles), len(section_progress))

        weak_concepts = [
            WeakConcept(concept=concept, score=data["score"], sections=sorted(data["sections"]))
            for concept, data in concept_scores.items()
        ]
        weak_concepts.sort(key=lambda item: (-item.score, item.concept))
        weak_concepts = weak_concepts[:5]

        review_sections = [
            item.section_id
            for item in sorted(
                (section for section in section_progress if section.is_weak),
                key=lambda section: (section.accuracy if section.accuracy is not None else 1.0, -section.help_requested_count),
            )
        ]

        accuracy = round(total_correct / total_scored, 3) if total_scored else None
        completion_rate = round(min(answered_sections / total_sections, 1.0), 3) if total_sections else 0.0
        review_titles = [titles.get(section_id, section_id) for section_id in review_sections]

        return SessionSummaryResponse(
            session_id=session_id,
            lesson_id=lesson_id,
            total_events=len(events),
            total_answered=total_answered,
            total_correct=total_correct,
            total_scored=total_scored,
            accuracy=accuracy,
            help_requested_count=help_requested,
            total_time_spent_seconds=total_time,
            answered_sections=answered_sections,
            total_sections=total_sections,
            completion_rate=completion_rate,
            section_progress=section_progress,
            weak_concepts=weak_concepts,
            review_sections=review_sections,
            summary_text=_summary_text(
                answered_sections=answered_sections,
                total_sections=total_sections,
                total_correct=total_correct,
                total_scored=total_scored,
                weak_concepts=[item.concept for item in weak_concepts],
                review_titles=review_titles,
            ),
        )

    def _require_session(self, lesson_id: str, session_id: str) -> dict:
        session = self.repository.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        if normalize_lesson_id(session["lesson_id"]) != normalize_lesson_id(lesson_id):
            raise ValueError(f"Session {session_id} does not belong to lesson {lesson_id}")
        return session


class InMemoryLearningService:
    """In-memory storage kept for lightweight event-contract tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}

    def create_session(self, lesson_id: str, _request: CreateSessionRequest) -> SessionResponse:
        session_id = f"session_{uuid4().hex[:12]}"
        self._sessions[session_id] = {
            "session_id": session_id,
            "lesson_id": lesson_id,
            "state": {},
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._events[session_id] = []
        return SessionResponse(session_id=session_id, lesson_id=lesson_id, state={})

    def submit_event(self, lesson_id: str, session_id: str, request: SubmitEventRequest) -> EventResponse:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")

        event_id = f"event_{uuid4().hex[:12]}"
        self._events[session_id].append(
            {
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
        )
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
        return SessionStateResponse(
            session_id=session_id,
            lesson_id=lesson_id,
            total_events=len(events),
            interaction_summary=build_interaction_summary(events),
        )

    def list_events(self, lesson_id: str, session_id: str) -> list[dict]:
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        session = self._sessions[session_id]
        if session["lesson_id"] != lesson_id:
            raise ValueError(f"Session {session_id} does not belong to lesson {lesson_id}")
        return [dict(event) for event in self._events.get(session_id, [])]


def _empty_section(section_id: str, title: str | None) -> dict:
    return {
        "section_id": section_id,
        "title": title,
        "answered_count": 0,
        "correct_count": 0,
        "scored_count": 0,
        "help_requested_count": 0,
        "time_spent_seconds": 0,
    }


def _finalize_section(section: dict) -> SectionProgress:
    scored = section["scored_count"]
    return SectionProgress(
        **section,
        accuracy=round(section["correct_count"] / scored, 3) if scored else None,
    )


def _add_concept_scores(
    concept_scores: dict[str, dict],
    concepts: list[str],
    section_id: str,
    *,
    points: int,
) -> None:
    for concept in concepts:
        entry = concept_scores.setdefault(concept, {"score": 0, "sections": set()})
        entry["score"] += points
        entry["sections"].add(section_id)


def _summary_text(
    *,
    answered_sections: int,
    total_sections: int,
    total_correct: int,
    total_scored: int,
    weak_concepts: list[str],
    review_titles: list[str],
) -> str:
    parts: list[str] = []
    if total_sections:
        parts.append(f"已完成 {answered_sections}/{total_sections} 个章节")
    if total_scored:
        parts.append(f"答对 {total_correct}/{total_scored} 题")
    if weak_concepts:
        parts.append("薄弱概念：" + "、".join(weak_concepts[:3]))
    if review_titles:
        parts.append("建议重点复习：" + "、".join(review_titles[:3]))
    if not parts:
        return "尚无学习记录。"
    return "；".join(parts) + "。"


_learning_service: LearningService | None = None


def get_learning_service() -> LearningService:
    global _learning_service
    if _learning_service is None:
        # Imported lazily: the task service owns the shared engine and is created
        # by the content-generation API module at startup.
        from app.api.content_generation import task_service

        _learning_service = LearningService(SQLModelLearningRepository(task_service.repository.engine))
    return _learning_service
