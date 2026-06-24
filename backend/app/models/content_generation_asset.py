from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.content_generation_task import utc_now


class ContentGenerationAsset(SQLModel, table=True):
    __tablename__ = "content_generation_asset"

    id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(index=True, max_length=64)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    asset_type: str = Field(index=True, max_length=32)
    provider: str | None = Field(default=None, max_length=64)
    model: str | None = Field(default=None, max_length=128)
    asset_url: str = Field(max_length=512)
    storage_key: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    status: str = Field(index=True, max_length=32)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
