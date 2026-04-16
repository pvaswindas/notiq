from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Notiq"
    app_mode: str = Field(default="api", alias="APP_MODE")
    database_url: str = Field(default="postgresql+asyncpg://notiq:notiq@localhost:5432/notiq", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    worker_id: str = Field(default="worker-1", alias="WORKER_ID")
    worker_batch_size: int = Field(default=50, alias="WORKER_BATCH_SIZE")
    worker_poll_interval_seconds: float = Field(default=1.0, alias="WORKER_POLL_INTERVAL_SECONDS")
    worker_lease_seconds: int = Field(default=30, alias="WORKER_LEASE_SECONDS")
    max_events_per_minute: int = Field(default=120, alias="MAX_EVENTS_PER_MINUTE")
    delivery_workspace_rate_limit_per_minute: int = Field(default=100, alias="DELIVERY_WORKSPACE_RATE_LIMIT_PER_MINUTE")
    delivery_channel_rate_limit_per_minute: int = Field(default=0, alias="DELIVERY_CHANNEL_RATE_LIMIT_PER_MINUTE")
    delivery_rate_limit_window_seconds: int = Field(default=60, alias="DELIVERY_RATE_LIMIT_WINDOW_SECONDS")
    delivery_rate_limit_backoff_seconds: int = Field(default=30, alias="DELIVERY_RATE_LIMIT_BACKOFF_SECONDS")
    idempotency_ttl_seconds: int = Field(default=3600, alias="IDEMPOTENCY_TTL_SECONDS")
    admin_jwt_secret: str = Field(default="change-me-in-production", alias="ADMIN_JWT_SECRET")
    admin_jwt_algorithm: str = Field(default="HS256", alias="ADMIN_JWT_ALGORITHM")
    admin_jwt_exp_minutes: int = Field(default=60, alias="ADMIN_JWT_EXP_MINUTES")


settings = Settings()
