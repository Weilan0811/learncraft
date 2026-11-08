from app.content_types.registry import get_content_type_profile
from app.core.config import Settings, get_settings
from app.core.provider_config import Capability, ensure_capabilities
from app.schemas.request import ContentGenerationRequest


def required_capabilities(request: ContentGenerationRequest) -> tuple[Capability, ...]:
    """Return the providers a single request actually depends on."""
    profile = get_content_type_profile(request.content_type)
    allowed_elements = profile.element_policy.allowed_elements
    capabilities: list[Capability] = ["text"]
    if "image" in allowed_elements and request.generation_options.include_images:
        capabilities.append("image")
    if "audio_file" in allowed_elements:
        capabilities.append("tts")
    return tuple(capabilities)


def ensure_request_providers_ready(
    request: ContentGenerationRequest,
    settings: Settings | None = None,
) -> None:
    current = settings or get_settings()
    ensure_capabilities(current, required_capabilities(request))
