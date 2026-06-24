from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationEvent(SQLModel, table=True):
    __tablename__ = "content_generation_event"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(index=True, max_length=64)
    event_type: str = Field(index=True, max_length=64)
    node: str | None = Field(default=None, index=True, max_length=128)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
