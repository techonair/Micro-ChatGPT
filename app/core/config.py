from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ai-chatbot-backend"
    environment: Literal["dev", "staging", "prod"] = "dev"
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot"

    openai_api_key: str | None = None
    openai_default_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    llama_api_base_url: str | None = None
    llama_api_key: str | None = None

    openai_context_limit: int = 12000
    anthropic_context_limit: int = 180000
    llama_context_limit: int = 8000

    sql_pool_size: int = 10
    sql_max_overflow: int = 20
    sql_pool_timeout: int = 30
    sql_pool_recycle: int = 1800

    log_level: str = Field(default="INFO")

    @property
    def provider_context_limits(self) -> dict[str, int]:
        return {
            "openai": self.openai_context_limit,
            "anthropic": self.anthropic_context_limit,
            "llama3": self.llama_context_limit,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
