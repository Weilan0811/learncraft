import time
from contextvars import ContextVar
from typing import Any

from app.schemas.observability import GenerationMetric

_pending_provider_calls: ContextVar[tuple[dict[str, Any], ...]] = ContextVar("pending_provider_calls", default=())


def monotonic_ms() -> int:
    return int(time.monotonic() * 1000)


def _usage_int(usage: dict[str, object], *keys: str) -> int | None:
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int):
            return value
    return None


def build_node_metric(
    *,
    task_id: str,
    node: str,
    unit_id: str | None = None,
    duration_ms: int | None = None,
    fallback_reason: str | None = None,
    error_type: str | None = None,
    metadata: dict[str, object] | None = None,
) -> GenerationMetric:
    return GenerationMetric(
        task_id=task_id,
        node=node,
        unit_id=unit_id,
        duration_ms=duration_ms,
        fallback_used=bool(fallback_reason),
        fallback_reason=fallback_reason,
        error_type=error_type,
        metadata=metadata or {},
    )


def build_provider_metric(
    *,
    task_id: str,
    node: str,
    unit_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    usage: dict[str, object] | None = None,
    retry_count: int = 0,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> GenerationMetric:
    usage = usage or {}
    return GenerationMetric(
        task_id=task_id,
        node=node,
        unit_id=unit_id,
        provider=provider,
        model=model,
        duration_ms=duration_ms,
        prompt_tokens=_usage_int(usage, "prompt_tokens", "input_tokens"),
        completion_tokens=_usage_int(usage, "completion_tokens", "output_tokens"),
        total_tokens=_usage_int(usage, "total_tokens"),
        retry_count=retry_count,
        metadata=dict(metadata or {}),
    )


def record_provider_call(
    *,
    provider: str,
    model: str,
    usage: dict[str, object] | None = None,
    retry_count: int = 0,
    metadata: dict[str, Any] | None = None,
) -> None:
    pending = _pending_provider_calls.get()
    _pending_provider_calls.set(
        (
            *pending,
            {
                "provider": provider,
                "model": model,
                "usage": dict(usage or {}),
                "retry_count": retry_count,
                "metadata": dict(metadata or {}),
            },
        )
    )


def drain_provider_metrics(*, task_id: str, node: str, unit_id: str | None = None) -> list[GenerationMetric]:
    pending = _pending_provider_calls.get()
    _pending_provider_calls.set(())
    return [
        build_provider_metric(
            task_id=task_id,
            node=node,
            unit_id=unit_id,
            provider=str(call.get("provider")) if call.get("provider") else None,
            model=str(call.get("model")) if call.get("model") else None,
            usage=call.get("usage") if isinstance(call.get("usage"), dict) else {},
            retry_count=int(call.get("retry_count") or 0),
            metadata=call.get("metadata") if isinstance(call.get("metadata"), dict) else {},
        )
        for call in pending
    ]
