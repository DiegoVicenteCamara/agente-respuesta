"""Herramientas del agente de voz expuestas al LLM en tiempo real.

Cada delegación pasa primero por el triaje Sistema 1 (Jev):

- ``fast``: se responde directo con el modelo económico, sin tocar Celery.
- ``orchestrator``: se despacha la tarea al equipo de subagentes (Celery).
- ``block``: inyección de instrucciones detectada; rechazo cortés, sin enviar.
- ``propose_commit``: riesgo crítico; se pide confirmación explícita
  (``confirm_execution``) antes de ejecutar.
- ``cancel_task``: revoca por voz la tarea Celery activa de la sesión.
"""

import logging
import time
import uuid
from contextvars import ContextVar

from livekit.agents import RunContext, function_tool

from backend.bus import redis_client
from backend.decision import respond, router
from backend.decision.schemas import RouteAction
from backend.orchestrator import cost

logger = logging.getLogger(__name__)

#: Identidad del usuario de la sesión de voz activa (issue #8).
#: Lo fija ``voice_entrypoint`` al resolver participante > claims > anonymous.
USER_ID: ContextVar[str | None] = ContextVar("voice_user_id", default=None)

BLOCK_MESSAGE = (
    "No puedo ejecutar esa solicitud: parece contener intentos de manipular mis "
    "instrucciones. Reformúlala de otra forma por favor."
)
PROPOSE_MESSAGE = (
    "Antes de ejecutar esto necesito tu confirmación: {goal}. ¿Confirmo?"
)
NO_PENDING_MESSAGE = "No hay ninguna acción pendiente de confirmación."
CANCELLED_MESSAGE = "De acuerdo, cancelo esa acción."
LAUNCH_MESSAGE = (
    "He lanzado a mi equipo de subagentes con el objetivo: {goal}. "
    "Te iré avisando por aquí en cuanto tengan avances."
)
CONFIRMED_MESSAGE = (
    "Confirmado. He lanzado a mi equipo de subagentes con el objetivo: {goal}. "
    "Te iré avisando por aquí en cuanto tengan avances."
)
NO_ACTIVE_TASK_MESSAGE = "No tengo ninguna tarea en curso que cancelar."
CANCEL_TASK_MESSAGE = "He cancelado la tarea en curso: {goal}."

# Ejecuciones pendientes de confirmación (Propose-Commit), clave: sesión.
PENDING: dict[str, dict] = {}
# Tarea Celery activa por sesión, clave: sesión.
ACTIVE_TASKS: dict[str, dict] = {}


def _session_key(ctx) -> str:
    return f"session-{id(ctx.session)}"


async def _fast_answer(task_id: str, goal: str, model: str) -> str:
    async with cost.tracked():
        answer = await respond.quick_answer(goal, model=model)
        await cost.publish_cost_ready(task_id, model)
        return answer


def _dispatch_orchestrator(task_id: str, goal: str, user_id: str | None = None) -> None:
    from backend.orchestrator.tasks import celery_app

    args = [task_id, goal] if user_id is None else [task_id, goal, user_id]
    celery_app.send_task("run_pipeline", args=args, task_id=task_id)
    logger.info("Tarea delegada: task_id=%s goal=%r user_id=%r", task_id, goal, user_id)


def _revoke_task(task_id: str) -> None:
    from backend.orchestrator.tasks import celery_app

    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")


def _register_active(ctx, task_id: str, goal: str) -> None:
    """Guarda la tarea activa de la sesión, revocando la anterior si existía."""
    key = _session_key(ctx)
    previous = ACTIVE_TASKS.pop(key, None)
    if previous is not None:
        _safe_revoke(str(previous["task_id"]))
    ACTIVE_TASKS[key] = {"task_id": task_id, "goal": goal}


def _safe_revoke(task_id: str) -> None:
    try:
        _revoke_task(task_id)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo revocar la tarea task_id=%s", task_id)


async def _publish_task_cancelled(task_id: str, goal: str) -> None:
    payload = {
        "task_id": task_id,
        "type": "task_cancelled",
        "agent": "orchestrator",
        "message": f"Tarea cancelada: {goal}",
        "priority": "info",
        "ts": int(time.time() * 1000),
    }
    try:
        await redis_client.publish_event(payload)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo publicar task_cancelled task_id=%s", task_id)


async def delegate_complex_task_core(ctx, goal: str) -> str:
    """Decide el ruteo de la delegación y devuelve el texto a leer al usuario."""
    task_id = str(uuid.uuid4())
    decision = await router.route(task_id, goal)
    if decision.action == RouteAction.FAST:
        return await _fast_answer(task_id, goal, decision.model)
    if decision.action == RouteAction.BLOCK:
        return BLOCK_MESSAGE
    if decision.action == RouteAction.PROPOSE_COMMIT:
        PENDING[_session_key(ctx)] = {"goal": goal}
        return PROPOSE_MESSAGE.format(goal=goal)
    try:
        _dispatch_orchestrator(task_id, goal, USER_ID.get())
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo despachar la tarea a Celery")
        raise RuntimeError(f"No se pudo lanzar el equipo de subagentes: {exc}") from exc
    _register_active(ctx, task_id, goal)
    return LAUNCH_MESSAGE.format(goal=goal)


async def confirm_execution_core(ctx, confirm: bool) -> str:
    """Resuelve una ejecución pendiente de Propose-Commit según la confirmación."""
    key = _session_key(ctx)
    pending = PENDING.pop(key, None)
    if pending is None:
        return NO_PENDING_MESSAGE
    if not confirm:
        return CANCELLED_MESSAGE
    goal = str(pending["goal"])
    task_id = str(uuid.uuid4())
    decision = await router.route(task_id, goal)
    if decision.action == RouteAction.BLOCK:
        return BLOCK_MESSAGE
    if decision.action == RouteAction.FAST:
        return await _fast_answer(task_id, goal, decision.model)
    try:
        _dispatch_orchestrator(task_id, goal, USER_ID.get())
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo despachar la tarea a Celery")
        raise RuntimeError(f"No se pudo lanzar el equipo de subagentes: {exc}") from exc
    _register_active(ctx, task_id, goal)
    return CONFIRMED_MESSAGE.format(goal=goal)


async def cancel_task_core(ctx) -> str:
    """Revoca la tarea Celery activa de la sesión y publica ``task_cancelled``."""
    active = ACTIVE_TASKS.pop(_session_key(ctx), None)
    if active is None:
        return NO_ACTIVE_TASK_MESSAGE
    task_id = str(active["task_id"])
    goal = str(active["goal"])
    _safe_revoke(task_id)
    await _publish_task_cancelled(task_id, goal)
    return CANCEL_TASK_MESSAGE.format(goal=goal)


@function_tool()
async def delegate_complex_task(ctx: RunContext, goal: str) -> str:
    """Delega un objetivo complejo a un equipo de subagentes que trabajan en
    segundo plano (búsqueda web y síntesis) y que avisan por voz cuando hay
    novedades. Las tareas simples se responden directamente en el momento.

    Args:
        goal: Descripción del objetivo o pregunta a investigar.
    """
    text = await delegate_complex_task_core(ctx, goal)
    await ctx.update(text)
    return ""


@function_tool()
async def confirm_execution(ctx: RunContext, confirm: bool) -> str:
    """Confirma o cancela una acción de alto riesgo pendiente de aprobación.

    Args:
        confirm: True para ejecutar la acción pendiente, False para cancelarla.
    """
    text = await confirm_execution_core(ctx, confirm)
    await ctx.update(text)
    return ""


@function_tool()
async def cancel_task(ctx: RunContext) -> str:
    """Cancela la tarea en curso que los subagentes están ejecutando en segundo
    plano. Úsala cuando el usuario pida parar, detener o cancelar el trabajo
    actual.
    """
    text = await cancel_task_core(ctx)
    await ctx.update(text)
    return ""