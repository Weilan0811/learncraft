from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, MySQLDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    kb_provider: Literal["external", "local"] = "external"
    tts_model: str = "qwen3-tts-instruct-flash"
    tts_person1_voice: str = "Ethan"
    tts_person2_voice: str = "Cherry"
    tts_output_format: str = "mp3"
    podcast_segment_max_retries: int = 1
    podcast_segment_retry_delay_seconds: float = 10.0

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

    kb_api_base_url: str = ""
    kb_api_key: str | None = None
    kb_retrieval_top_k: int = 5
    kb_max_chars_per_item: int = 8000
    kb_request_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_prefix="CONTENT_GENERATOR_", env_file=".env")

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
