from app.core.task import TaskStatus
from app.schemas.state import ContentGenerationState


def normalize_request(state: ContentGenerationState) -> dict[str, object]:
    options = state.raw_request.get("generation_options", {}) if state.raw_request else {}
    normalized = {
        "content_type": state.content_type,
        "topic": state.topic.strip(),
        "user_prompt": state.user_prompt.strip(),
        "language": str(options.get("language", "zh-CN")) if isinstance(options, dict) else "zh-CN",
        "difficulty": str(options.get("difficulty", "introductory")) if isinstance(options, dict) else "introductory",
        "style": str(options.get("style", "educational")) if isinstance(options, dict) else "educational",
    }
    return {
        "normalized_request": normalized,
        "current_node": "normalize_request",
        "status": TaskStatus.running,
        "progress": {"current_stage": "normalizing", "percent": 5},
    }
