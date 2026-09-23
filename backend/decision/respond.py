"""Respuesta directa con el modelo económico para la ruta FAST (Tier Low)."""

from __future__ import annotations

from backend.config import settings
from backend.orchestrator import nodes

QUICK_ANSWER_SYSTEM_PROMPT = (
    "Eres «Respuesta», un asistente de voz. Responde de forma directa, concisa y "
    "natural en español a la consulta del usuario, como en una llamada telefónica. "
    "No describas tu proceso, no uses herramientas ni menciones a otros agentes: "
    "esta es una respuesta simple de un solo paso."
)


async def quick_answer(goal: str, model: str | None = None) -> str:
    """Devuelve la respuesta del modelo económico a una tarea de complejidad baja."""
    answer = await nodes.chat(
        goal, QUICK_ANSWER_SYSTEM_PROMPT, model=model or settings.openai_fast_model
    )
    return answer.strip() or (
        "No tengo una respuesta preparada para eso; puedo investigarlo con mi equipo "
        "si quieres."
    )