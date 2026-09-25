"""Recolección ligera de tokens y coste estimado por tarea.

Un ``CostTracker`` por tarea (contextvar) acumula el uso de tokens registrado
por el callback de LangChain; al cerrar la tarea se publica el evento
``cost_ready`` con el coste estimado en euros. Con ``COST_TRACKING_ENABLED``
desactivado no se añade ningún callback y no se emite el evento.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from langchain_core.callbacks import BaseCallbackHandler

from backend.bus import redis_client
from backend.config import settings

logger = logging.getLogger(__name__)

_tracker: ContextVar["CostTracker | None"] = ContextVar("cost_tracker", default=None)


@dataclass
class ModelUsage:
    model: str
    tokens_in: int
    tokens_out: int


@dataclass
class CostTracker:
    """Acumulador del uso por modelo dentro de una misma tarea."""

    samples: list[ModelUsage] = field(default_factory=list)

    def add(self, model: str, tokens_in: int, tokens_out: int) -> None:
        if tokens_in < 0 or tokens_out < 0:
            return
        self.samples.append(ModelUsage(model, tokens_in, tokens_out))

    def totals(self) -> tuple[int, int]:
        return (
            sum(s.tokens_in for s in self.samples),
            sum(s.tokens_out for s in self.samples),
        )


def current() -> CostTracker | None:
    """Devuelve el tracker activo de la tarea, si existe."""
    return _tracker.get()


@asynccontextmanager
async def tracked():
    """Contexto que abre y cierra un tracker para la tarea en curso."""
    token = _tracker.set(CostTracker())
    try:
        yield _tracker.get()
    finally:
        _tracker.reset(token)


def _model_slug(model: str) -> str:
    return (model or "").upper().replace("-", "_").replace(".", "_")


def estimate_cost_eur(model: str, tokens_in: int, tokens_out: int) -> float:
    """Coste estimado en euros según la tabla USD configurable y el factor EUR."""
    price_in, price_out = settings.pricing_usd.get(_model_slug(model), (0.0, 0.0))
    usd = tokens_in / 1_000_000 * price_in + tokens_out / 1_000_000 * price_out
    return round(usd * settings.cost_eur_per_usd, 6)


def _tiktoken_encoding(model: str):
    try:
        import tiktoken

        try:
            return tiktoken.encoding_for_model(model)
        except Exception:  # noqa: BLE001
            return tiktoken.get_encoding("cl100k_base")
    except Exception as exc:  # noqa: BLE001
        logger.debug("tiktoken no disponible (%s)", exc)
        return None


def _usage_from_response(response) -> tuple[int, int] | None:
    """Extrae (in, out) de ``usage_metadata`` o de ``llm_output.token_usage``."""
    try:
        message = response.generations[0][0].message
        usage = getattr(message, "usage_metadata", None) or {}
        tin, tout = usage.get("input_tokens"), usage.get("output_tokens")
        if tin is not None and tout is not None:
            return int(tin), int(tout)
    except Exception:  # noqa: BLE001
        pass
    try:
        llm_output = getattr(response, "llm_output", None) or {}
        usage = llm_output.get("token_usage") or {}
        tin, tout = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if tin is not None and tout is not None:
            return int(tin), int(tout)
    except Exception:  # noqa: BLE001
        pass
    return None


class TokenUsageCallback(BaseCallbackHandler):
    """Callback de LangChain que registra el uso de tokens en el tracker activo.

    Prioriza la metadata del proveedor y, a falta de ella, estima con tiktoken.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        self._prompts_in: int | None = None

    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        encoding = _tiktoken_encoding(self.model)
        if encoding is not None:
            self._prompts_in = sum(len(encoding.encode(str(p))) for p in prompts)

    def on_llm_end(self, response, **kwargs) -> None:
        usage = _usage_from_response(response)
        if usage is None:
            encoding = _tiktoken_encoding(self.model)
            if encoding is None:
                return
            try:
                tokens_out = sum(len(encoding.encode(g.text)) for g in response.generations[0])
            except Exception:  # noqa: BLE001
                return
            tokens_in = self._prompts_in or 0
        else:
            tokens_in, tokens_out = usage
        tracker = current()
        if tracker is not None:
            tracker.add(self.model, tokens_in, tokens_out)


async def publish_cost_ready(task_id: str, model: str) -> None:
    """Publica el evento ``cost_ready`` (silent) al cerrar la tarea."""
    if not settings.cost_tracking_enabled:
        return
    tracker = current()
    tokens_in, tokens_out = tracker.totals() if tracker else (0, 0)
    cost_eur = estimate_cost_eur(model, tokens_in, tokens_out)
    payload = {
        "task_id": task_id,
        "type": "cost_ready",
        "agent": "cost",
        "message": (
            f"Coste estimado: {cost_eur:.4f} € "
            f"({tokens_in} tokens in / {tokens_out} tokens out)"
        ),
        "priority": "silent",
        "model": model,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_eur": cost_eur,
        "estimated": True,
    }
    try:
        await redis_client.publish_event(payload)
    except ConnectionError:
        logger.warning("Redis no disponible; el evento cost_ready no se publicó")
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo publicar el evento cost_ready")