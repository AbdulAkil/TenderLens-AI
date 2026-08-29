from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://tenderlens:change-me-in-production@postgres:5432/tenderlens"
    )
    ted_api_base_url: str = "https://api.ted.europa.eu"
    ted_api_timeout_seconds: float = 30.0
    ted_api_max_retries: int = 3
    ted_ingestion_enabled: bool = False
    document_processing_enabled: bool = False
    embedding_provider: str | None = None
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_enabled: bool = False
    llm_provider: str | None = None
    openai_llm_model: str = "gpt-5.4-mini"
    llm_enabled: bool = False
    reranker_provider: str = "keyword"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def api_cors_origins(self) -> list[str]:
        """Return the explicit browser origins permitted to call the local API."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
