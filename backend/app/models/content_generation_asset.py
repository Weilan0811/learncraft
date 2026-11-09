from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.core.asset import AssetStatus
from app.models.content_generation_task import utc_now


class ContentGenerationAsset(SQLModel, table=True):
    __tablename__ = "content_generation_asset"

    asset_id: str = Field(primary_key=True, max_length=64)
    task_id: str = Field(foreign_key="content_generation_task.task_id", index=True, max_length=64)
    unit_id: str | None = Field(default=None, index=True, max_length=128)
    asset_type: str = Field(index=True, max_length=32)
    uri: str = Field(max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    status: str = Field(default=AssetStatus.generated.value, index=True, max_length=32)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0, nullable=False)
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column("metadata", JSON, nullable=True))
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)

    @property
    def id(self) -> str:
        return self.asset_id
