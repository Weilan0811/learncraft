from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import SchemaModel


ResourceType = Literal["image", "audio"]
ResourceStatus = Literal["pending", "generating", "generated", "failed", "missing", "retrying"]


class TaskResource(SchemaModel):
    resource_id: str
    asset_type: ResourceType
    status: ResourceStatus
    unit_id: str | None = None
    title: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    retryable: bool = True
    retry_blocked_reason: str | None = None
    updated_at: datetime | None = None


class FailedResourceListResponse(SchemaModel):
    task_id: str
    resources: list[TaskResource] = Field(default_factory=list)


class ResourceRetryResponse(SchemaModel):
    task_id: str
    resource_id: str
    status: Literal["retrying"] = "retrying"
    retry_count: int = 0
