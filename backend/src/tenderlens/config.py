from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import model_validator
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
    environment: str = "development"
    site_url: str = "http://localhost:3000"
    session_cookie: str = "tenderlens_session"
    session_hours: int = 24
    trial_days: int = 14
    email_provider: str = "dry_run"
    email_api_key: str | None = None
    email_from: str = "TenderLens <onboarding@example.invalid>"
    email_sandbox_recipients: str = ""
    email_require_approval: bool = True
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_starter_price: str = ""
    stripe_professional_price: str = ""
    stripe_business_price: str = ""
    plans_json: str | None = None
    admin_emails: str = ""
    ingestion_query: str = "buyer-country = BEL"
    ingestion_max_notices: int = 500
    worker_poll_seconds: int = 10
    ai_monthly_budget_eur: float = 0
    ai_call_reservation_eur: float = 0.10
    ai_input_eur_per_million: float = 1
    ai_output_eur_per_million: float = 5
    support_email: str = ""

    @model_validator(mode="after")
    def validate_production(self):
        if self.production:
            if urlsplit(self.site_url).scheme != "https":
                raise ValueError("Production SITE_URL must use HTTPS")
            if (
                "change-me" in self.database_url
                or "local-development" in self.database_url
                or "localhost" in self.database_url
                or not urlsplit(self.database_url).password
            ):
                raise ValueError("Production DATABASE_URL must use explicit non-sample credentials")
            if not self.api_cors_origins or any(
                "localhost" in origin or "*" in origin or not origin.startswith("https://")
                for origin in self.api_cors_origins
            ):
                raise ValueError("Production CORS origins must be explicit HTTPS origins")
        if self.stripe_secret_key and not self.stripe_secret_key.startswith("sk_test_"):
            raise ValueError(
                "Only Stripe test-mode keys are supported until live activation is reviewed"
            )
        return self

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def api_cors_origins(self) -> list[str]:
        """Return the explicit browser origins permitted to call the local API."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
