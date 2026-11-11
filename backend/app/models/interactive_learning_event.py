from datetime import datetime
from typing import Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class InteractiveLearningEvent(SQLModel, table=True):
    __tablename__ = "interactive_learning_event"

    event_id: str = Field(primary_key=True, max_length=64)
    session_id: str = Field(
        foreign_key="interactive_learning_session.session_id",
        index=True,
        max_length=64,
    )
    lesson_id: str = Field(index=True, max_length=128)
    section_id: str = Field(index=True, max_length=128)
    block_id: str | None = Field(default=None, max_length=128)
    interaction_id: str | None = Field(default=None, max_length=128)
    event_type: str = Field(index=True, max_length=64)
    payload: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
