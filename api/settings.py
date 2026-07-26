"""Configuración de la API (cargada desde .env)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"
    # El juez de los evals debe ser al menos tan capaz como el agente que juzga,
    # y no tiene por qué ser el mismo modelo: usar el mismo enmascara sus
    # propios sesgos (se aprueba a sí mismo).
    judge_model: str = "claude-opus-4-8"
    duckdb_path: str = "data/radar.duckdb"

    # Embeddings locales (multilingües, corren en CPU). BGE-m3 = 1024 dims.
    # Cambiar de modelo implica ajustar `embedding_dim` y la dimensión del
    # esquema en search/schema.sql.
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024

    # Observabilidad. Sin claves, las trazas solo van al JSONL local
    # (ver api/observabilidad.py); el agente funciona igual.
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "radar"
    postgres_user: str = "radar"
    postgres_password: str = "change-me"

    # Auth. HS256 con secreto simétrico: suficiente para un único servicio
    # (no hay necesidad de las claves pública/privada de RS256).
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Billing (Stripe). Sin claves, /billing/* devuelve error explícito en vez
    # de fallar a medias (ver api/billing.py); el resto de la API funciona
    # igual. Los price_id se crean en el dashboard de Stripe, uno por plan de
    # pago (ver api/planes.py).
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_basico: str = ""
    stripe_price_pro: str = ""
    stripe_price_ilimitado: str = ""
    billing_success_url: str = "http://localhost:8000/billing/exito"
    billing_cancel_url: str = "http://localhost:8000/billing/cancelado"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
