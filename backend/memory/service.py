"""Servicio de memoria persistente de conversaciones por usuario (issue #8).

La memoria vive en Redis (clave ``user:{user_id}:memory`` con TTL) y es un
servicio por debajo del grafo: tanto el plano de voz (saludo) como el plano de
ejecución (planner inyecta, synthesize guarda) la consumen sin acoplarse.

Con ``MEMORY_ENABLED=false`` todas las operaciones son no-op y el flujo actual
queda intacto.
"""

import logging
import time
from typing import Any

from backend.bus import redis_client
from backend.config import settings
from backend.orchestrator.nodes import chat

logger = logging.getLogger(__name__)

MEMORY_SYSTEM_PROMPT = (
    "Eres el módulo de memoria de un asistente de voz. Actualiza el resumen de "
    "conversaciones del usuario: conserva los temas y preferencias ya conocidos "
    "e incorpora lo nuevo. Responde con un único párrafo conciso en español, "
    "sin encabezados ni voces."
)

_TTL_DAYS_TO_SECONDS = 86400


def _key(user_id: str) -> str:
    return f"user:{user_id}:memory"


def _ttl_seconds(ttl_days: int | None = None) -> int:
    days = ttl_days or settings.memory_ttl_days
    return max(1, days) * _TTL_DAYS_TO_SECONDS


async def load(user_id: str | None) -> str | None:
    """Devuelve el resumen persistido del usuario, o ``None``."""
    if not settings.memory_enabled or not user_id:
        return None
    return redis_client.mem_get(_key(user_id))


async def store(user_id: str | None, summary: str | None, ttl_days: int | None = None) -> None:
    """Persiste el resumen del usuario con TTL configurable."""
    if not settings.memory_enabled or not user_id or not summary:
        return
    redis_client.mem_set(_key(user_id), summary, _ttl_seconds(ttl_days))


async def summarize(goal: str, analysis: str, previous: str | None) -> str:
    """Actualiza el resumen del usuario con LLM; fallback determinista."""
    if not settings.memory_enabled:
        return _deterministic(goal, analysis)
    prompt = (
        f"Contexto previo del usuario: {previous or '(ninguno)'}\n\n"
        f"Objetivo de esta conversación: {goal}\n\nHallazgos: {analysis}"
    )
    try:
        summary = await chat(prompt, MEMORY_SYSTEM_PROMPT)
    except Exception:  # noqa: BLE001
        logger.exception("summarize LLM falló; usando resumen determinista")
        summary = ""
    if summary:
        return summary
    return _deterministic(goal, analysis)


async def publish_recalled(user_id: str | None, message: str | None) -> None:
    """Publica un evento ``memory_recalled`` (silent) para el panel debbuger."""
    if not settings.memory_enabled or not user_id or not message:
        return
    payload: dict[str, Any] = {
        "user_id": user_id,
        "type": "memory_recalled",
        "agent": "orchestrator",
        "message": message,
        "priority": "silent",
        "ts": int(time.time() * 1000),
    }
    try:
        await redis_client.publish_event(payload)
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo publicar memory_recalled para %s", user_id)


def _deterministic(goal: str, analysis: str) -> str:
    raw = f"{goal}: {analysis}".strip()
    max_chars = max(0, settings.memory_max_chars)
    return raw[:max_chars] if max_chars else raw