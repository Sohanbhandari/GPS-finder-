from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "GPS Vehicle Tracking System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database Credentials & Connection
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "gps_tracker"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gps_tracker"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/gps_tracker"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # JWT Security Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # MQTT Telemetry Transport Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_CLIENT_ID: str = "fastapi_gps_consumer"

    # Business Thresholds
    ONLINE_THRESHOLD_SECONDS: int = 60

    # Logging Level
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
