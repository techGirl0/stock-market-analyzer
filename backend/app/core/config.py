from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WolfStreet Signal API"
    api_prefix: str = "/api/v1"
    market_data_provider: str = "demo"
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "development-only-change-me"
    database_url: str = "sqlite+aiosqlite:///backend/data/app.db"
    llm_provider: str = "disabled"
    groq_api_key: str | None = None
    groq_model: str = "qwen/qwen3.8-27b"
    provider_cache_seconds: int = 60
    provider_max_stale_seconds: int = 300
    provider_request_budget: int = 60
    provider_budget_window_seconds: int = 60
    api_rate_limit: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_production(self) -> None:
        if self.jwt_secret == "development-only-change-me":
            raise ValueError("JWT_SECRET must be changed outside development")
        if self.market_data_provider == "demo":
            raise ValueError("MARKET_DATA_PROVIDER must be configured outside development")


@lru_cache
def get_settings() -> Settings:
    return Settings()
