from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationArtifact(SQLModel, table=True):
    __tablename__ = "content_generation_artifact"

    artifact_id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(foreign_key="content_generation_task.task_id", index=True, max_length=64)
    artifact_type: str = Field(index=True, max_length=32)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    version: int = Field(default=1, nullable=False)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)

    @property
    def id(self) -> str:
        return self.artifact_id
