from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Content Generator Agent"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    storage_backend: str = "local"
    storage_root: str = "storage"
    asset_public_base_url: str = "/api/assets"
    # TODO(MVP-config): Add provider/storage settings for LLM, image generation,
    # vector retrieval, object storage, and async task queue backends.

    model_config = SettingsConfigDict(env_prefix="CONTENT_GENERATOR_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
