"""Configuración de la API (cargada desde .env)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"
    duckdb_path: str = "data/radar.duckdb"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "radar"
    postgres_user: str = "radar"
    postgres_password: str = "change-me"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
