"""Política de notificación proactiva por voz.

Lógica pura (sin dependencias de LiveKit) para decidir si un evento de los
subagentes debe interrumpir la conversación y cómo expresarlo, siguiendo los
principios de la investigación (prioridad, puntos de quiebre y asertividad).
"""

SILENT = "silent"
INFO = "info"
URGENT = "urgent"


def classify(payload: dict) -> str:
    return payload.get("priority", INFO)


def build_spoken_update(payload: dict) -> str | None:
    """Devuelve el texto a hablar para un evento, o ``None`` si debe callar."""
    priority = classify(payload)
    if priority == SILENT:
        return None
    message = str(payload.get("message", "")).strip()
    if not message:
        return None
    if priority == URGENT:
        return f"Necesito tu atención. {message}"
    return f"Disculpa que te interrumpa, {message}"