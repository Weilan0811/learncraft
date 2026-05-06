from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Content Generator Agent"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_prefix="CONTENT_GENERATOR_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
