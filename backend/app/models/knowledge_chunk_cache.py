from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class KnowledgeChunkCache(SQLModel, table=True):
    __tablename__ = "knowledge_chunk_cache"

    chunk_id: str = Field(primary_key=True, max_length=64)
    text: str = Field(sa_type=LONGTEXT().with_variant(Text(), "sqlite"), nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    last_seen_at: datetime = Field(default_factory=utc_now, nullable=False)
