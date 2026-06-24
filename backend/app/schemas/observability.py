from pydantic import Field

from app.schemas.base import SchemaModel


class GenerationMetric(SchemaModel):
    task_id: str
    node: str
    unit_id: str | None = None
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    error_type: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
