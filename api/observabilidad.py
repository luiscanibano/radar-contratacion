"""Trazas del agente: qué hizo, cuánto tardó y cuánto costó.

La semana 5 dejó el agente funcionando pero `answer()` tiraba a la basura toda
la telemetría: cuántos turnos hizo, qué herramientas usó, cuántos tokens gastó
y si el caché de prompt estaba sirviendo. Aquí se recoge eso en un objeto
`Traza` de datos puros (sin dependencias de red), y se emite a dos sitios:

- **JSONL local** (`data/trazas.jsonl`): siempre, sin configurar nada.
- **Langfuse**: solo si hay claves en `.env`. Si falla la red o las claves son
  malas, se registra y se sigue: la observabilidad nunca debe tumbar el agente.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from api.settings import settings

log = logging.getLogger(__name__)

# Precios de la Claude API en USD por millón de tokens (input, output).
# Fuente: platform.claude.com/docs/en/pricing. Actualizar al cambiar de modelo.
PRECIOS_USD_POR_MTOK: dict[str, tuple[float, float]] = {
    "claude-fable-5": (10.00, 50.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-opus-4-7": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Sonnet 5 tiene precio de lanzamiento hasta el 31/08/2026. Es lo que se factura
# de verdad hoy, así que se aplica por fecha en vez de codificar un número que
# se volvería silenciosamente falso en septiembre.
_PRECIO_INTRO: dict[str, tuple[tuple[float, float], date]] = {
    "claude-sonnet-5": ((2.00, 10.00), date(2026, 8, 31)),
}

# Multiplicadores de caché de prompt sobre el precio de input.
_MULT_CACHE_READ = 0.1  # servir desde caché
_MULT_CACHE_WRITE = 1.25  # escribir en caché (TTL de 5 min)

RUTA_TRAZAS = Path("data/trazas.jsonl")


def precios(modelo: str, cuando: date | None = None) -> tuple[float, float]:
    """Precio (input, output) en USD/MTok del modelo en una fecha dada."""
    intro = _PRECIO_INTRO.get(modelo)
    if intro is not None:
        tarifa, ultimo_dia = intro
        if (cuando or date.today()) <= ultimo_dia:
            return tarifa
    if modelo not in PRECIOS_USD_POR_MTOK:
        raise KeyError(
            f"Modelo sin precio conocido: {modelo!r}. "
            f"Añádelo a PRECIOS_USD_POR_MTOK en api/observabilidad.py."
        )
    return PRECIOS_USD_POR_MTOK[modelo]


@dataclass
class LlamadaModelo:
    """Una llamada a `messages.create()` dentro del bucle de tool use."""

    turno: int
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    latencia_s: float = 0.0
    stop_reason: str | None = None

    def coste_usd(self, modelo: str, cuando: date | None = None) -> float:
        precio_in, precio_out = precios(modelo, cuando)
        entrada = (
            self.input_tokens
            + self.cache_read_input_tokens * _MULT_CACHE_READ
            + self.cache_creation_input_tokens * _MULT_CACHE_WRITE
        )
        return (entrada * precio_in + self.output_tokens * precio_out) / 1_000_000


@dataclass
class UsoTool:
    """Una ejecución de herramienta pedida por el modelo."""

    turno: int
    nombre: str
    entrada: dict[str, Any]
    latencia_s: float = 0.0
    ok: bool = True
    filas: int | None = None
    error: str | None = None


@dataclass
class Traza:
    """Todo lo observable de una pregunta, de principio a fin."""

    pregunta: str
    modelo: str
    respuesta: str = ""
    llamadas: list[LlamadaModelo] = field(default_factory=list)
    tools: list[UsoTool] = field(default_factory=list)
    latencia_total_s: float = 0.0
    error: str | None = None

    @property
    def turnos(self) -> int:
        return len(self.llamadas)

    @property
    def tools_usadas(self) -> list[str]:
        """Nombres de herramientas en orden de uso, sin duplicados."""
        vistas: list[str] = []
        for t in self.tools:
            if t.nombre not in vistas:
                vistas.append(t.nombre)
        return vistas

    @property
    def tokens_entrada(self) -> int:
        return sum(
            ll.input_tokens + ll.cache_read_input_tokens + ll.cache_creation_input_tokens
            for ll in self.llamadas
        )

    @property
    def tokens_salida(self) -> int:
        return sum(ll.output_tokens for ll in self.llamadas)

    @property
    def tokens_cache_leidos(self) -> int:
        return sum(ll.cache_read_input_tokens for ll in self.llamadas)

    @property
    def ratio_cache(self) -> float:
        """Fracción de tokens de entrada servidos desde caché (0..1).

        Si esto se queda en 0 llamada tras llamada, el `cache_control` del
        SYSTEM_PROMPT no está funcionando (ver `api/agent/graph.py`).
        """
        total = self.tokens_entrada
        return self.tokens_cache_leidos / total if total else 0.0

    @property
    def coste_usd(self) -> float:
        return sum(ll.coste_usd(self.modelo) for ll in self.llamadas)

    def resumen(self) -> dict[str, Any]:
        """Vista plana para logs, informes de evals y tablas."""
        return {
            "pregunta": self.pregunta,
            "modelo": self.modelo,
            "turnos": self.turnos,
            "tools_usadas": self.tools_usadas,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "ratio_cache": round(self.ratio_cache, 3),
            "coste_usd": round(self.coste_usd, 6),
            "latencia_total_s": round(self.latencia_total_s, 3),
            "error": self.error,
        }


def _a_dict(traza: Traza) -> dict[str, Any]:
    d = dataclasses.asdict(traza)
    d.update(traza.resumen())
    return d


def _escribir_jsonl(traza: Traza, ruta: Path | None = None) -> None:
    # Se lee el global aquí y no como valor por defecto del parámetro: un
    # default se congela al definir la función y haría imposible redirigir la
    # ruta (tests, o un despliegue que la cambie en caliente).
    ruta = ruta or RUTA_TRAZAS
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_a_dict(traza), ensure_ascii=False, default=str) + "\n")


def langfuse_configurado() -> bool:
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def _cliente_langfuse():
    from langfuse import Langfuse

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def _fin(inicio_ns: int, latencia_s: float) -> int:
    """Instante de fin en ns que reproduce la duración medida.

    Las trazas se emiten a Langfuse *después* de que la pregunta termine, así
    que el instante de inicio de cada span es el de emisión, no el real. Las
    duraciones sí son exactas porque se fijan con `end_time`.
    """
    return inicio_ns + int(latencia_s * 1_000_000_000)


def _emitir_langfuse(traza: Traza) -> None:
    cliente = _cliente_langfuse()
    raiz = cliente.start_observation(
        name="preguntar",
        as_type="agent",
        input=traza.pregunta,
        output=traza.respuesta,
        metadata=traza.resumen(),
        level="ERROR" if traza.error else "DEFAULT",
        status_message=traza.error,
    )
    inicio_ns = time.time_ns()
    try:
        for llamada in traza.llamadas:
            hijo = raiz.start_observation(
                name=f"claude turno {llamada.turno}",
                as_type="generation",
                model=traza.modelo,
                usage_details={
                    "input": llamada.input_tokens,
                    "output": llamada.output_tokens,
                    "cache_read_input_tokens": llamada.cache_read_input_tokens,
                    "cache_creation_input_tokens": llamada.cache_creation_input_tokens,
                },
                cost_details={"total": llamada.coste_usd(traza.modelo)},
                metadata={"stop_reason": llamada.stop_reason},
            )
            hijo.end(end_time=_fin(inicio_ns, llamada.latencia_s))
        for uso in traza.tools:
            hijo = raiz.start_observation(
                name=uso.nombre,
                as_type="tool",
                input=uso.entrada,
                output={"filas": uso.filas} if uso.ok else {"error": uso.error},
                level="ERROR" if not uso.ok else "DEFAULT",
                status_message=uso.error,
            )
            hijo.end(end_time=_fin(inicio_ns, uso.latencia_s))
    finally:
        raiz.end(end_time=_fin(inicio_ns, traza.latencia_total_s))
        cliente.flush()


def emitir(traza: Traza) -> None:
    """Persiste la traza. Nunca lanza: un fallo de telemetría no es un fallo del agente."""
    try:
        _escribir_jsonl(traza)
    except OSError as exc:  # noqa: BLE001 — disco lleno / permisos no deben tumbar la respuesta
        log.warning("No se pudo escribir la traza en %s: %s", RUTA_TRAZAS, exc)

    if not langfuse_configurado():
        return
    try:
        _emitir_langfuse(traza)
    except Exception as exc:  # noqa: BLE001 — red, claves inválidas, cambios de API de Langfuse
        log.warning("No se pudo enviar la traza a Langfuse: %s", exc)
