from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RequiMind AI API"
    app_version: str = "0.1.0"
    app_version: str = "0.1.0"
    llm_mode: str = "local"  # local | ollama (100% offline)
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
