"""Esquema tipado de la capa de decisión (triaje Sistema 1 / Jev).

Define los enums y modelos del triaje y de la decisión de ruteo, independientes
de ``langchain-typesafe`` para que la política sea pura y fácil de testear.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# IDs de las preguntas evaluadas por Jev en una sola llamada.
Q_TARGET_WORKER = "target_worker"
Q_COMPLEXITY_TIER = "complexity_tier"
Q_RISK_INDEX = "risk_index"
Q_INJECTION = "is_prompt_injection"


class TargetWorker(str, Enum):
    """Trabajador de dominio al que debe atenderse la solicitud.

    Hoy solo ``dialogue`` (respuesta directa por voz) y ``research`` (orquestador
    LangGraph) tienen worker real; el resto queda reservado para dominios futuros
    y se enrutan al orquestador/escalada.
    """

    DIALOGUE = "dialogue"
    RESEARCH = "research"
    BILLING = "billing"
    IDENTITY = "identity"
    SUPPORT = "support"


class ComplexityTier(str, Enum):
    """Complejidad operativa de la tarea: decide el costo del modelo."""

    LOW = "low"
    HIGH = "high"


class RouteAction(str, Enum):
    """Acción de despacho resultante de la política de ruteo."""

    FAST = "fast"
    ORCHESTRATOR = "orchestrator"
    BLOCK = "block"
    PROPOSE_COMMIT = "propose_commit"


class TriageAnswer(BaseModel):
    """Respuesta normalizada del clasificador Sistema 1 (Jev)."""

    target_worker: TargetWorker
    complexity_tier: ComplexityTier
    risk_index: float = Field(ge=0.0, le=2.0)
    is_prompt_injection: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class RouteDecision(BaseModel):
    """Decisión de ruteo: acción, modelo y contexto para observabilidad."""

    action: RouteAction
    reason: str
    task_id: str = ""
    model: str = ""
    tier: ComplexityTier | None = None
    risk: float = 0.0
    injection: float = 0.0
    worker: TargetWorker | None = None
    confidence: float = 0.0
    latency_ms: int = 0
    fallback: bool = False
    detail: str | None = None


class RoutingConfig:
    """Umbrales de la política de ruteo, con valores por defecto calibrados."""

    def __init__(
        self,
        risk_fast: float = 0.5,
        risk_critical: float = 1.5,
        injection_threshold: float = 0.85,
        confidence_min: float = 0.6,
    ) -> None:
        self.risk_fast = risk_fast
        self.risk_critical = risk_critical
        self.injection_threshold = injection_threshold
        self.confidence_min = confidence_min

    @classmethod
    def from_settings(cls) -> "RoutingConfig":
        from backend.config import settings

        return cls(
            risk_fast=settings.routing_risk_fast,
            risk_critical=settings.routing_risk_critical,
            injection_threshold=settings.routing_injection_threshold,
            confidence_min=settings.routing_confidence_min,
        )


class DecisionNormalizationError(ValueError):
    """La respuesta de Jev no pudo normalizarse a un triaje estricto."""