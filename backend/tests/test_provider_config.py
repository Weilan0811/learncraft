from pathlib import Path

import pytest
from sqlalchemy.engine import make_url
from sqlmodel import Session, select

from app.core.config import PROJECT_ROOT, Settings
from app.core.provider_config import ProviderConfigurationError, check_capability, redact_secrets
from app.models import ContentGenerationTask
from app.schemas.request import ContentGenerationRequest
from app.services.provider_readiness import ensure_request_providers_ready, required_capabilities
from app.services.task_repository import SQLModelTaskRepository
from app.services.task_service import PersistentTaskService


PROVIDER_ENV_VARS = [
    "CONTENT_GENERATOR_PROVIDER_MODE",
    "CONTENT_GENERATOR_DATABASE_URL",
    "CONTENT_GENERATOR_APIMART_API_KEY",
    "CONTENT_GENERATOR_BAILIAN_API_KEY",
    "CONTENT_GENERATOR_DEEPSEEK_API_KEY",
    "DB_PASSWORD",
]


@pytest.fixture
def clean_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in PROVIDER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def build_request(content_type: str, **options: object) -> ContentGenerationRequest:
    return ContentGenerationRequest(
        content_type=content_type,
        topic="配置检查",
        user_prompt="生成一段测试内容",
        generation_options=options or {},
    )


def test_env_example_boots_with_sqlite_and_stub(clean_provider_env: None) -> None:
    settings = Settings(_env_file=PROJECT_ROOT / ".env.example")

    assert settings.provider_mode == "stub"
    assert make_url(settings.DATABASE_URL).get_backend_name() == "sqlite"
    assert Path(make_url(settings.DATABASE_URL).database) == PROJECT_ROOT / "storage" / "tasks.db"
    assert Path(settings.storage_root) == PROJECT_ROOT / "storage"


def test_relative_runtime_paths_resolve_against_project_root(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_DATABASE_URL", "sqlite:///storage/check.db")
    monkeypatch.setenv("CONTENT_GENERATOR_STORAGE_ROOT", "storage")
    monkeypatch.setenv("CONTENT_GENERATOR_LOG_ROOT", "storage/logs")
    monkeypatch.setenv("CONTENT_GENERATOR_DEBUG_ROOT", "storage/debug_workflow")

    settings = Settings(_env_file=None)

    assert Path(settings.storage_root) == PROJECT_ROOT / "storage"
    assert Path(settings.log_root) == PROJECT_ROOT / "storage" / "logs"
    assert Path(settings.debug_root) == PROJECT_ROOT / "storage" / "debug_workflow"
    assert Path(make_url(settings.DATABASE_URL).database) == PROJECT_ROOT / "storage" / "check.db"


def test_in_memory_sqlite_url_is_not_rewritten(
    clean_provider_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTENT_GENERATOR_DATABASE_URL", "sqlite:///:memory:")

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL == "sqlite:///:memory:"


def test_stub_mode_requires_no_provider_credentials(clean_provider_env: None) -> None:
    settings = Settings(_env_file=None, provider_mode="stub")

    for capability in ("text", "image", "tts"):
        assert check_capability(settings, capability) == []


def test_real_mode_reports_missing_text_key(clean_provider_env: None) -> None:
    settings = Settings(_env_file=None, provider_mode="real", text_provider=" DeepSeek ")

    issues = check_capability(settings, "text")

    assert settings.text_provider == "deepseek"
    assert issues
    assert issues[0].env_vars == ("CONTENT_GENERATOR_DEEPSEEK_API_KEY",)


def test_real_mode_reports_missing_image_key_for_bailian(clean_provider_env: None) -> None:
    settings = Settings(_env_file=None, provider_mode="real", image_provider="bailian")

    issues = check_capability(settings, "image")

    assert issues
    assert "CONTENT_GENERATOR_BAILIAN_API_KEY" in issues[0].env_vars


def test_real_mode_rejects_unsupported_tts_output_format(clean_provider_env: None) -> None:
    settings = Settings(
        _env_file=None,
        provider_mode="real",
        bailian_api_key="sk-test-key",
        tts_output_format="ogg",
    )

    issues = check_capability(settings, "tts")

    assert issues
    assert issues[0].env_vars == ("CONTENT_GENERATOR_TTS_OUTPUT_FORMAT",)


def test_required_capabilities_follow_fixed_content_type_policy() -> None:
    assert required_capabilities(build_request("podcast_script")) == ("text", "tts")
    assert required_capabilities(build_request("interactive_html")) == ("text",)
    assert required_capabilities(build_request("lecture")) == ("text", "image")
    assert required_capabilities(build_request("slide_deck")) == ("text", "image")
    assert required_capabilities(build_request("social_post")) == ("text", "image")


def test_missing_providers_only_block_related_content_types(clean_provider_env: None) -> None:
    settings = Settings(_env_file=None, provider_mode="real", text_provider="bailian")

    with pytest.raises(ProviderConfigurationError) as podcast_error:
        ensure_request_providers_ready(build_request("podcast_script"), settings=settings)
    assert "CONTENT_GENERATOR_BAILIAN_API_KEY" in str(podcast_error.value)
    assert "CONTENT_GENERATOR_APIMART_API_KEY" not in str(podcast_error.value)

    with pytest.raises(ProviderConfigurationError) as lecture_error:
        ensure_request_providers_ready(build_request("lecture"), settings=settings)
    assert "CONTENT_GENERATOR_APIMART_API_KEY" in str(lecture_error.value)

    ensure_request_providers_ready(build_request("interactive_html"), settings=Settings(
        _env_file=None, provider_mode="real", text_provider="bailian", bailian_api_key="sk-test-key"
    ))


def test_create_task_is_rejected_before_persisting_when_provider_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_provider_env: None
) -> None:
    settings = Settings(_env_file=None, provider_mode="real", text_provider="deepseek")
    monkeypatch.setattr("app.services.provider_readiness.get_settings", lambda: settings)
    repository = SQLModelTaskRepository(database_url=f"sqlite:///{tmp_path / 'tasks.db'}", echo=False)
    service = PersistentTaskService(repository=repository)

    with pytest.raises(ProviderConfigurationError):
        service.create_task(build_request("interactive_html"))

    with Session(repository.engine) as session:
        assert session.exec(select(ContentGenerationTask)).all() == []


def test_redact_secrets_removes_configured_keys(clean_provider_env: None) -> None:
    settings = Settings(_env_file=None, provider_mode="real", bailian_api_key="sk-very-secret-key")

    redacted = redact_secrets("调用失败：sk-very-secret-key 已失效", settings)

    assert "sk-very-secret-key" not in redacted
    assert "***" in redacted
