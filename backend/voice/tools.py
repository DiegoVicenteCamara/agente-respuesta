"""Herramientas del agente de voz expuestas al LLM en tiempo real."""

import logging
import uuid

from livekit.agents import RunContext, function_tool

logger = logging.getLogger(__name__)


@function_tool()
async def delegate_complex_task(ctx: RunContext, goal: str) -> str:
    """Delega un objetivo complejo a un equipo de subagentes que trabajan en
    segundo plano (búsqueda web y síntesis) y que avisan por voz cuando hay
    novedades.

    Args:
        goal: Descripción del objetivo o pregunta a investigar.
    """
    task_id = str(uuid.uuid4())
    try:
        from backend.orchestrator.tasks import celery_app

        celery_app.send_task("run_pipeline", args=[task_id, goal])
        logger.info("Tarea delegada: task_id=%s goal=%r", task_id, goal)
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo despachar la tarea a Celery")
        raise RuntimeError(f"No se pudo lanzar el equipo de subagentes: {exc}") from exc

    await ctx.update(
        f"He lanzado a mi equipo de subagentes con el objetivo: {goal}. "
        "Te iré avisando por aquí en cuanto tengan avances."
    )
    # El aviso se ha dado con ctx.update; no repetimos texto al terminar.
    return ""