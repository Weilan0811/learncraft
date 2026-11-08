from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, MySQLDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


# backend/app/core/config.py -> repository root; relative runtime paths and the
# .env file must resolve the same way no matter which directory starts the app.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_project_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def _resolve_sqlite_url(database_url: str) -> str:
    try:
        url = make_url(database_url)
    except Exception:
        return database_url
    if url.get_backend_name() != "sqlite":
        return database_url
    database = url.database
    if not database or database == ":memory:":
        return database_url
    path = Path(database)
    if path.is_absolute():
        return database_url
    return url.set(database=(PROJECT_ROOT / path).resolve().as_posix()).render_as_string(hide_password=False)


def ensure_sqlite_parent_directory(database_url: str) -> None:
    """SQLite cannot create missing parent directories; do it before connecting."""
    try:
        url = make_url(database_url)
    except Exception:
        return
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return
    path = Path(url.database)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    app_name: str = "Content Generator Agent"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    storage_backend: str = "local"
    storage_root: str = "storage"
    asset_public_base_url: str = "/api/assets"
    database_url: str | None = Field(default=None, validation_alias=AliasChoices("CONTENT_GENERATOR_DATABASE_URL", "DATABASE_URL"))
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("DB_HOST", "CONTENT_GENERATOR_DB_HOST"))
    db_port: int = Field(default=3306, validation_alias=AliasChoices("DB_PORT", "CONTENT_GENERATOR_DB_PORT"))
    db_username: str = Field(default="root", validation_alias=AliasChoices("DB_USERNAME", "CONTENT_GENERATOR_DB_USERNAME"))
    db_password: str = Field(default="", validation_alias=AliasChoices("DB_PASSWORD", "CONTENT_GENERATOR_DB_PASSWORD"))
    db_database: str = Field(default="future_learning", validation_alias=AliasChoices("DB_DATABASE", "CONTENT_GENERATOR_DB_DATABASE"))
    db_log_echo: bool = Field(default=False, validation_alias=AliasChoices("DB_LOG_ECHO", "CONTENT_GENERATOR_DB_LOG_ECHO"))
    log_root: str = Field(default="storage/logs", validation_alias=AliasChoices("LOG_ROOT", "CONTENT_GENERATOR_LOG_ROOT"))
    debug_root: str = Field(default="storage/debug_workflow", validation_alias=AliasChoices("DEBUG_ROOT", "CONTENT_GENERATOR_DEBUG_ROOT"))

    provider_mode: Literal["stub", "real"] = "stub"
    allow_fallback: bool = False

    text_provider: str = "bailian"
    text_model: str = "qwen3.5-flash"
    image_provider: str = "apimart"
    image_model: str = "gpt-image-2"
    image_resolution: Literal["1k", "2k", "4k"] = "1k"
    tts_provider: str = "bailian"
    tts_model: str = "qwen3-tts-instruct-flash"
    tts_person1_voice: str = "Ethan"
    tts_person2_voice: str = "Cherry"
    tts_output_format: str = "mp3"
    podcast_segment_max_retries: int = 1
    podcast_segment_retry_delay_seconds: float = 10.0
    # Single-process deployments can safely mark leftover tasks as interrupted
    # on startup. Disable this when running several workers against one database.
    recover_interrupted_tasks: bool = True

    apimart_api_key: str | None = None
    apimart_base_url: str = "https://api.apimart.ai/v1"
    bailian_api_key: str | None = None
    bailian_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    bailian_tts_base_url: str = "https://dashscope.aliyuncs.com"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"

    request_timeout_seconds: float = 60.0
    max_retries: int = 2
    generation_unit_concurrency: int = 3
    image_generation_concurrency: int = 3
    tts_generation_concurrency: int = 4
    provider_rate_limit_backoff_seconds: float = 2.0

    apimart_image_poll_interval_seconds: float = 2.0
    apimart_image_poll_timeout_seconds: float = 180.0

    model_config = SettingsConfigDict(env_prefix="CONTENT_GENERATOR_", env_file=PROJECT_ROOT / ".env")

    @model_validator(mode="after")
    def resolve_runtime_paths(self) -> "Settings":
        self.storage_root = _resolve_project_path(self.storage_root)
        self.log_root = _resolve_project_path(self.log_root)
        self.debug_root = _resolve_project_path(self.debug_root)
        self.text_provider = self.text_provider.strip().lower()
        self.image_provider = self.image_provider.strip().lower()
        self.tts_provider = self.tts_provider.strip().lower()
        self.tts_output_format = self.tts_output_format.strip().lower()
        if self.database_url:
            self.database_url = _resolve_sqlite_url(self.database_url)
        return self

    @property
    def DATABASE_URL(self) -> str:
        if self.database_url:
            return self.database_url
        return str(
            MySQLDsn.build(
                scheme="mysql+pymysql",
                username=self.db_username,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                path=self.db_database,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
