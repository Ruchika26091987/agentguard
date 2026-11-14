from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentGuard Gateway"
    environment: str = "development"
    default_ttl_seconds: int = 3600
    budget_limit_per_minute: int = 100
    enable_pii_scrubbing: bool = True
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_prefix="AGENTGUARD_", case_sensitive=False)


settings = Settings()
