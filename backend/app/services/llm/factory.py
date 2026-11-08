from app.core.config import Settings, get_settings
from app.core.provider_config import ensure_capability
from app.services.llm.base import LLMService
from app.services.llm.openai_compatible import BailianLLMService, DeepseekLLMService, StubLLMService


def get_llm_service(settings: Settings | None = None) -> LLMService:
    settings = settings or get_settings()
    if settings.provider_mode == "stub":
        return StubLLMService()
    ensure_capability(settings, "text")
    if settings.text_provider == "bailian":
        return BailianLLMService(
            api_key=settings.bailian_api_key or "",
            model=settings.text_model,
            base_url=settings.bailian_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            max_retries=settings.max_retries,
        )
    if settings.text_provider == "deepseek":
        return DeepseekLLMService(
            api_key=settings.deepseek_api_key or "",
            model=settings.text_model,
            base_url=settings.deepseek_base_url,
            timeout_seconds=settings.request_timeout_seconds,
            max_retries=settings.max_retries,
        )
    raise ValueError(f"Unsupported text provider: {settings.text_provider}")
