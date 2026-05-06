from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Content Generator Agent"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    storage_backend: str = "local"
    storage_root: str = "storage"
    asset_public_base_url: str = "/api/assets"

    provider_mode: Literal["stub", "real"] = "stub"

    text_provider: str = "bailian"
    text_model: str = "qwen3.5-flash"
    image_provider: str = "apimart"
    image_model: str = "gpt-image-2"
    image_resolution: Literal["1k", "2k", "4k"] = "1k"
    embedding_provider: str = "bailian"
    embedding_model: str = "text-embedding-v3"

    apimart_api_key: str | None = None
    apimart_base_url: str = "https://api.apimart.ai/v1"
    bailian_api_key: str | None = None
    bailian_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    request_timeout_seconds: float = 60.0
    max_retries: int = 2

    apimart_image_poll_interval_seconds: float = 2.0
    apimart_image_poll_timeout_seconds: float = 180.0

    qdrant_path: str = "storage/qdrant_data"
    qdrant_collection: str = "default"
    retrieval_top_k: int = 5
    max_retrieval_chars: int = 6000

    model_config = SettingsConfigDict(env_prefix="CONTENT_GENERATOR_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
