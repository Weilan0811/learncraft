from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationReference(SQLModel, table=True):
    __tablename__ = "content_generation_reference"
    __table_args__ = (
        UniqueConstraint("task_id", "unit_id", "chunk_id", "source_path", name="uq_reference_dedup"),
    )

    reference_id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(foreign_key="content_generation_task.task_id", index=True, max_length=64)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    chunk_id: str = Field(foreign_key="knowledge_chunk_cache.chunk_id", index=True, max_length=64)
    source_path: str = Field(max_length=512)
    source_title: str | None = Field(default=None, max_length=255)
    rank: int | None = Field(default=None)
    score: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    @property
    def id(self) -> str:
        return self.reference_id
