"""Configuración de la API (cargada desde .env)."""

from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valores de fábrica que solo son aceptables en desarrollo local. Si llegan a
# producción (típicamente porque el .env real no se cargó: typo, permisos,
# volumen mal montado) dejarían la API con un secreto de JWT forjable por
# cualquiera o una contraseña de Postgres trivial — mejor no arrancar.
_VALORES_INSEGUROS = {"change-me"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "desarrollo" (por defecto, para no romper el flujo local) o "produccion".
    # Se fija con ENTORNO=produccion en el .env del VPS.
    entorno: str = "desarrollo"

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
    billing_portal_return_url: str = "http://localhost:8000/app#cuenta"

    # Alertas por email. Sin clave, el job de alertas falla al enviar (no al
    # buscar) y lo registra sin tumbar las demás alertas (ver api/alertas.py).
    resend_api_key: str = ""
    alert_from_email: str = "alertas@radarcontratacion.com"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @model_validator(mode="after")
    def _rechazar_secretos_de_fabrica_en_produccion(self) -> Settings:
        if self.entorno != "produccion":
            return self
        inseguros = [
            nombre
            for nombre, valor in (
                ("JWT_SECRET", self.jwt_secret),
                ("POSTGRES_PASSWORD", self.postgres_password),
            )
            if valor in _VALORES_INSEGUROS
        ]
        if inseguros:
            raise RuntimeError(
                "ENTORNO=produccion pero estas variables siguen en su valor de "
                f"fábrica (revisa que el .env se está cargando): {', '.join(inseguros)}"
            )
        return self


settings = Settings()
