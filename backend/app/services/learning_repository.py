"""SQLModel persistence for interactive learning sessions and events."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.models.interactive_learning_event import InteractiveLearningEvent
from app.models.interactive_learning_session import InteractiveLearningSession


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _session_payload(session: InteractiveLearningSession) -> dict:
    return {
        "session_id": session.session_id,
        "lesson_id": session.lesson_id,
        "state": dict(session.state or {}),
        "created_at": _iso(session.created_at),
        "updated_at": _iso(session.updated_at),
    }


def _event_payload(event: InteractiveLearningEvent) -> dict:
    return {
        "event_id": event.event_id,
        "session_id": event.session_id,
        "lesson_id": event.lesson_id,
        "section_id": event.section_id,
        "block_id": event.block_id,
        "interaction_id": event.interaction_id,
        "event_type": event.event_type,
        "payload": dict(event.payload or {}),
        "created_at": _iso(event.created_at),
    }


class SQLModelLearningRepository:
    """Learning persistence sharing the application's existing engine."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create_session(self, lesson_id: str) -> dict:
        session = InteractiveLearningSession(
            session_id=f"session_{uuid4().hex[:12]}",
            lesson_id=lesson_id,
            state={},
        )
        with Session(self.engine) as db:
            db.add(session)
            db.commit()
            db.refresh(session)
            return _session_payload(session)

    def get_session(self, session_id: str) -> dict | None:
        with Session(self.engine) as db:
            session = db.get(InteractiveLearningSession, session_id)
            return _session_payload(session) if session else None

    def list_events(self, session_id: str) -> list[dict]:
        with Session(self.engine) as db:
            statement = (
                select(InteractiveLearningEvent)
                .where(InteractiveLearningEvent.session_id == session_id)
                .order_by(InteractiveLearningEvent.created_at, InteractiveLearningEvent.event_id)
            )
            return [_event_payload(event) for event in db.exec(statement).all()]

    def add_event(
        self,
        *,
        session_id: str,
        lesson_id: str,
        section_id: str,
        block_id: str | None,
        interaction_id: str | None,
        event_type: str,
        payload: dict,
    ) -> dict:
        event = InteractiveLearningEvent(
            event_id=f"event_{uuid4().hex[:12]}",
            session_id=session_id,
            lesson_id=lesson_id,
            section_id=section_id,
            block_id=block_id,
            interaction_id=interaction_id,
            event_type=event_type,
            payload=payload,
        )
        with Session(self.engine) as db:
            db.add(event)
            session = db.get(InteractiveLearningSession, session_id)
            if session is not None:
                session.updated_at = _now()
                db.add(session)
            db.commit()
            db.refresh(event)
            return _event_payload(event)
