from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RequiMind AI API"
    app_version: str = "0.1.0"
    llm_mode: str = "local"  # local | ollama | gemini (100% offline if local/ollama)
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"
    cors_origins: str = "*"
    
    # Database Configuration
    shield_db_mode: str = "json"  # json | mongodb
    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_db_name: str = "the_shield"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
