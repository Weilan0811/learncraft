from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings
from app.core.exceptions import ContentGeneratorError


Capability = Literal["text", "image", "tts"]

CAPABILITY_LABELS: dict[Capability, str] = {
    "text": "文本服务",
    "image": "图片服务",
    "tts": "语音服务",
}

_SECRET_FIELDS = ("apimart_api_key", "bailian_api_key", "deepseek_api_key", "kb_api_key")


@dataclass(frozen=True)
class ProviderIssue:
    capability: Capability
    env_vars: tuple[str, ...]
    message: str


class ProviderConfigurationError(ContentGeneratorError):
    """Raised when a task needs a real provider that is not configured."""

    def __init__(self, issues: list[ProviderIssue]) -> None:
        self.issues = issues
        super().__init__("；".join(issue.message for issue in issues))


def check_capability(settings: Settings, capability: Capability) -> list[ProviderIssue]:
    if settings.provider_mode == "stub":
        return []
    label = CAPABILITY_LABELS[capability]
    if capability == "text":
        provider = settings.text_provider.strip().lower()
        if provider == "bailian":
            key_var, key_value = "CONTENT_GENERATOR_BAILIAN_API_KEY", settings.bailian_api_key
        elif provider == "deepseek":
            key_var, key_value = "CONTENT_GENERATOR_DEEPSEEK_API_KEY", settings.deepseek_api_key
        else:
            return [_unsupported_issue(capability, "CONTENT_GENERATOR_TEXT_PROVIDER", provider, ("bailian", "deepseek"))]
        model_var, model = "CONTENT_GENERATOR_TEXT_MODEL", settings.text_model
    elif capability == "image":
        provider = settings.image_provider.strip().lower()
        if provider == "apimart":
            key_var, key_value = "CONTENT_GENERATOR_APIMART_API_KEY", settings.apimart_api_key
        elif provider == "bailian":
            key_var, key_value = "CONTENT_GENERATOR_BAILIAN_API_KEY", settings.bailian_api_key
        else:
            return [_unsupported_issue(capability, "CONTENT_GENERATOR_IMAGE_PROVIDER", provider, ("apimart", "bailian"))]
        model_var, model = "CONTENT_GENERATOR_IMAGE_MODEL", settings.image_model
    else:
        provider = settings.tts_provider.strip().lower()
        if provider != "bailian":
            return [_unsupported_issue(capability, "CONTENT_GENERATOR_TTS_PROVIDER", provider, ("bailian",))]
        if settings.tts_output_format.strip().lower() not in {"mp3", "wav"}:
            return [
                ProviderIssue(
                    capability=capability,
                    env_vars=("CONTENT_GENERATOR_TTS_OUTPUT_FORMAT",),
                    message=f"{label}配置无效：CONTENT_GENERATOR_TTS_OUTPUT_FORMAT 仅支持 mp3 或 wav。",
                )
            ]
        key_var, key_value = "CONTENT_GENERATOR_BAILIAN_API_KEY", settings.bailian_api_key
        model_var, model = "CONTENT_GENERATOR_TTS_MODEL", settings.tts_model

    missing: list[str] = []
    if not model.strip():
        missing.append(model_var)
    if not key_value or not key_value.strip():
        missing.append(key_var)
    if capability == "tts":
        if not settings.tts_person1_voice.strip():
            missing.append("CONTENT_GENERATOR_TTS_PERSON1_VOICE")
        if not settings.tts_person2_voice.strip():
            missing.append("CONTENT_GENERATOR_TTS_PERSON2_VOICE")
    if not missing:
        return []
    return [
        ProviderIssue(
            capability=capability,
            env_vars=tuple(missing),
            message=f"{label}未配置完整：请设置 {'、'.join(missing)}。",
        )
    ]


def check_capabilities(settings: Settings, capabilities: tuple[Capability, ...]) -> list[ProviderIssue]:
    issues: list[ProviderIssue] = []
    for capability in capabilities:
        issues.extend(check_capability(settings, capability))
    return issues


def ensure_capability(settings: Settings, capability: Capability) -> None:
    issues = check_capability(settings, capability)
    if issues:
        raise ProviderConfigurationError(issues)


def ensure_capabilities(settings: Settings, capabilities: tuple[Capability, ...]) -> None:
    issues = check_capabilities(settings, capabilities)
    if issues:
        raise ProviderConfigurationError(issues)


def describe_capability(settings: Settings, capability: Capability) -> str:
    if settings.provider_mode == "stub":
        return "stub 开发占位（不调用真实服务）"
    if capability == "text":
        provider, model = settings.text_provider, settings.text_model
    elif capability == "image":
        provider, model = settings.image_provider, settings.image_model
    else:
        provider, model = settings.tts_provider, settings.tts_model
    issues = check_capability(settings, capability)
    if issues:
        return f"{provider} / {model} 未就绪（{issues[0].message}）"
    return f"{provider} / {model} 已配置"


def redact_secrets(text: str, settings: Settings | None = None) -> str:
    current = settings or get_settings()
    redacted = text
    for field in _SECRET_FIELDS:
        value = getattr(current, field, None)
        if isinstance(value, str) and len(value) >= 4:
            redacted = redacted.replace(value, "***")
    passwords = {current.db_password}
    try:
        passwords.add(make_url(current.DATABASE_URL).password)
    except Exception:
        pass
    for password in passwords:
        if isinstance(password, str) and len(password) >= 4:
            redacted = redacted.replace(password, "***")
    return redacted


def masked_database_url(settings: Settings) -> str:
    try:
        return make_url(settings.DATABASE_URL).render_as_string(hide_password=True)
    except Exception:
        return "无法解析的数据库地址"


def _unsupported_issue(
    capability: Capability,
    env_var: str,
    value: str,
    options: tuple[str, ...],
) -> ProviderIssue:
    return ProviderIssue(
        capability=capability,
        env_vars=(env_var,),
        message=(
            f"{CAPABILITY_LABELS[capability]}配置无效：{env_var} 不支持“{value}”，"
            f"可选值为 {' / '.join(options)}。"
        ),
    )
