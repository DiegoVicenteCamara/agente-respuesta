"""Política de enrutamiento dual (FAST / ORCHESTRATOR / BLOCK / PROPOSE_COMMIT).

``decide`` es pura y testeable sin I/O. ``route`` clasifica con Jev, mide latencia
y publica un evento ``routing_decision`` (``priority: silent``) en el bus Redis.
"""

from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable

from backend.bus import redis_client
from backend.config import settings
from backend.decision import jev
from backend.decision.schemas import (
    ComplexityTier,
    RouteAction,
    RouteDecision,
    RoutingConfig,
    TargetWorker,
    TriageAnswer,
)

logger = logging.getLogger(__name__)

RISK_REVERSIBLE = 1.0

ClassifierT = Callable[[str], Awaitable["TriageAnswer | None"]]


def decide(
    triage: TriageAnswer,
    config: RoutingConfig,
    fast_model: str,
    advanced_model: str,
) -> RouteDecision:
    """Aplica los guardarraíles y determina la acción de despacho.

    Orden de precedencia (los guardarraíles nunca se degradan por baja confianza):
    1. Inyección de instrucciones -> BLOCK.
    2. Riesgo crítico (o reversible + tier high) -> PROPOSE_COMMIT.
    3. Confianza baja -> escalado conservador a ORCHESTRATOR.
    4. Worker de diálogo + tier low + riesgo bajo -> FAST (modelo económico).
    5. Resto -> ORCHESTRATOR (modelo avanzado si tier high).
    """
    injection = triage.is_prompt_injection
    risk = triage.risk_index
    high = triage.complexity_tier == ComplexityTier.HIGH

    if injection >= config.injection_threshold:
        return _decision(RouteAction.BLOCK, "injection_detected", triage, fast_model)

    if risk >= config.risk_critical or (risk >= RISK_REVERSIBLE and high):
        return _decision(
            RouteAction.PROPOSE_COMMIT, "critical_risk", triage, advanced_model
        )

    if triage.confidence < config.confidence_min:
        return _decision(
            RouteAction.ORCHESTRATOR, "low_confidence", triage, advanced_model if high else fast_model
        )

    if (
        triage.target_worker == TargetWorker.DIALOGUE
        and triage.complexity_tier == ComplexityTier.LOW
        and risk < config.risk_fast
    ):
        return _decision(RouteAction.FAST, "trivial_fast_path", triage, fast_model)

    return _decision(
        RouteAction.ORCHESTRATOR, "complex_task", triage, advanced_model if high else fast_model
    )


def _decision(
    action: RouteAction,
    reason: str,
    triage: TriageAnswer,
    model: str,
) -> RouteDecision:
    return RouteDecision(
        action=action,
        reason=reason,
        model=model,
        tier=triage.complexity_tier,
        risk=triage.risk_index,
        injection=triage.is_prompt_injection,
        worker=triage.target_worker,
        confidence=triage.confidence,
    )


def fallback_decision(
    task_id: str,
    *,
    fast_model: str,
    reason: str = "jev_unavailable",
) -> RouteDecision:
    """Decisión de fallback fail-open: todo se escala al orquestador."""
    logger.warning("Fallback de ruteo: %s", reason)
    return RouteDecision(
        action=RouteAction.ORCHESTRATOR,
        reason=reason,
        task_id=task_id,
        model=fast_model,
        fallback=True,
    )


async def route(
    task_id: str,
    goal: str,
    *,
    config: RoutingConfig | None = None,
    classify: ClassifierT = jev.classify,
    fast_model: str | None = None,
    advanced_model: str | None = None,
) -> RouteDecision:
    """Clasifica el ``goal``, decide el ruteo y publica el evento de observabilidad."""
    cfg = config or RoutingConfig.from_settings()
    fast = fast_model or settings.openai_fast_model
    advanced = advanced_model or settings.openai_advanced_model

    started = time.perf_counter()
    try:
        triage = await classify(goal)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Clasificador de Jev lanzó excepción (%s); fallback", exc)
        triage = None
    latency_ms = int((time.perf_counter() - started) * 1000)

    if triage is None:
        decision = fallback_decision(task_id, fast_model=fast)
    else:
        decision = decide(triage, cfg, fast, advanced)

    decision.task_id = task_id
    decision.latency_ms = latency_ms

    await _publish_event(decision)
    return decision


async def _publish_event(decision: RouteDecision) -> None:
    payload = {
        "task_id": decision.task_id,
        "type": "routing_decision",
        "agent": "jev-gate",
        "priority": "silent",
        "message": decision.reason,
        "route": decision.action.value,
        "tier": decision.tier.value if decision.tier else None,
        "risk": decision.risk,
        "injection": decision.injection,
        "confidence": decision.confidence,
        "worker": decision.worker.value if decision.worker else None,
        "model": decision.model,
        "latency_ms": decision.latency_ms,
        "fallback": decision.fallback,
    }
    try:
        await redis_client.publish_event(payload)
    except ConnectionError:
        logger.warning("Redis no disponible; el evento «routing_decision» no se publicó")
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo publicar el evento «routing_decision» en Redis")


__all__ = ["decide", "route", "fallback_decision", "RoutingConfig", "RouteDecision"]