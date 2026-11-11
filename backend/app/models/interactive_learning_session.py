from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class InteractiveLearningSession(SQLModel, table=True):
    __tablename__ = "interactive_learning_session"

    session_id: str = Field(primary_key=True, max_length=64)
    lesson_id: str = Field(index=True, max_length=128)
    state: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
