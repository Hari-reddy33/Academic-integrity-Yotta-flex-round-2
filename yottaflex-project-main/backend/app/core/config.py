from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://integrity:local-development-only@localhost:5432/integrity"
    jwt_secret: str = "local-development-secret-change-me"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:5173"
    seed_submissions: int = 10_000
    seed_flags: int = 1_000
    seed_cases: int = 300
    seed_seed: int = 20261022

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must use PostgreSQL with the psycopg driver.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
