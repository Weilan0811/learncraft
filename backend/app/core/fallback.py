from app.schemas.state import ContentGenerationState


def allow_generation_fallback(
    state: ContentGenerationState | None = None,
    normalized_request: dict[str, object] | None = None,
    provider_mode: str = "stub",
) -> bool:
    options = normalized_request
    if options is None and state is not None:
        options = state.normalized_request
    return provider_mode == "stub" or bool((options or {}).get("allow_fallback", False))


def fallback_detail(stage: str, exc: Exception, *, fallback_used: bool = True) -> dict[str, object]:
    return {
        "stage": stage,
        "code": type(exc).__name__,
        "message": str(exc),
        "detail": {"fallback_used": fallback_used},
        "recoverable": fallback_used,
    }
