"""Capa de filtrado, triaje y enrutamiento con Sistema 1 (Jev)."""

import logging

from backend.config import settings
from backend.decision import jev, respond, router  # noqa: F401
from backend.decision.jev import ClassifyOutcome  # noqa: F401
from backend.decision.schemas import (  # noqa: F401
    ComplexityTier,
    RouteAction,
    RouteDecision,
    RoutingConfig,
    TargetWorker,
    TriageAnswer,
)

if not settings.typesafe_api_key:
    logging.getLogger(__name__).warning(
        "TYPESAFE_API_KEY no configurada; el triaje Jev queda desactivado "
        "(todo escala al orquestador). Rellena .env y reinicia para activarlo."
    )

__all__ = [
    "jev",
    "respond",
    "router",
    "ClassifyOutcome",
    "ComplexityTier",
    "RouteAction",
    "RouteDecision",
    "RoutingConfig",
    "TargetWorker",
    "TriageAnswer",
]