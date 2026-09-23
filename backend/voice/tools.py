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

from livekit.agents import RunContext, function_tool

from backend.bus import redis_client
from backend.decision import respond, router
from backend.decision.schemas import RouteAction
from backend.orchestrator import cost

logger = logging.getLogger(__name__)

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

# Estado de sesión de voz (Propose-Commit + tarea Celery activa).
# Vive en Redis con TTL para que 2+ workers de voz compartan la misma
# sesión; la API pública del módulo no cambia.
SESSION_TTL_SECONDS = 3600


def _session_key(ctx) -> str:
    """Clave estable de sesión compartible entre workers.

    Orden: userdata explícito -> nombre/sid de la sala LiveKit ->
    atributo ``session_id`` (fakes/tests) -> ``id()`` como fallback.
    """
    session = getattr(ctx, "session", None)
    try:
        userdata = getattr(session, "userdata", None)
        if isinstance(userdata, dict):
            for field in ("session_id", "room", "room_name", "sid"):
                value = userdata.get(field)
                if value:
                    return f"session-{value}"
        elif isinstance(userdata, str) and userdata:
            return f"session-{userdata}"
    except Exception:  # noqa: BLE001
        pass
    try:
        room_io = getattr(session, "room_io", None)
        room = getattr(room_io, "room", None)
        if room is not None:
            name = getattr(room, "name", None) or getattr(room, "sid", None)
            if name:
                return f"session-{name}"
    except Exception:  # noqa: BLE001
        pass
    try:
        room = getattr(session, "room", None)
        if room is not None:
            name = (
                getattr(room, "name", None) or getattr(room, "sid", None) or str(room)
            )
            if name:
                return f"session-{name}"
    except Exception:  # noqa: BLE001
        pass
    try:
        sid = getattr(session, "session_id", None) or getattr(session, "id", None)
        if isinstance(sid, str) and sid:
            return f"session-{sid}"
    except Exception:  # noqa: BLE001
        pass
    return f"session-{id(session)}"


def _load_state(session_id: str) -> dict:
    try:
        data = redis_client.session_get(session_id)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo leer el estado de sesión %s", session_id)
        return {}
    return dict(data) if isinstance(data, dict) else {}


def _save_state(session_id: str, state: dict) -> None:
    try:
        if not state.get("pending") and not state.get("active"):
            redis_client.session_delete(session_id)
        else:
            redis_client.session_set(session_id, state, SESSION_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo guardar el estado de sesión %s", session_id)


async def _fast_answer(task_id: str, goal: str, model: str) -> str:
    async with cost.tracked():
        answer = await respond.quick_answer(goal, model=model)
        await cost.publish_cost_ready(task_id, model)
        return answer


def _dispatch_orchestrator(task_id: str, goal: str) -> None:
    from backend.orchestrator.tasks import celery_app

    celery_app.send_task("run_pipeline", args=[task_id, goal], task_id=task_id)
    logger.info("Tarea delegada: task_id=%s goal=%r", task_id, goal)


def _revoke_task(task_id: str) -> None:
    from backend.orchestrator.tasks import celery_app

    celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")


def _register_active(ctx, task_id: str, goal: str) -> None:
    """Guarda la tarea activa de la sesión, revocando la anterior si existía."""
    session_id = _session_key(ctx)
    state = _load_state(session_id)
    _set_active_in_state(state, task_id, goal)
    _save_state(session_id, state)


def _set_active_in_state(state: dict, task_id: str, goal: str) -> None:
    previous = state.get("active")
    if isinstance(previous, dict) and previous.get("task_id"):
        _safe_revoke(str(previous["task_id"]))
    state["active"] = {"task_id": task_id, "goal": goal}


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
        session_id = _session_key(ctx)
        state = _load_state(session_id)
        state["pending"] = {"goal": goal}
        _save_state(session_id, state)
        return PROPOSE_MESSAGE.format(goal=goal)
    try:
        _dispatch_orchestrator(task_id, goal)
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo despachar la tarea a Celery")
        raise RuntimeError(f"No se pudo lanzar el equipo de subagentes: {exc}") from exc
    _register_active(ctx, task_id, goal)
    return LAUNCH_MESSAGE.format(goal=goal)


async def confirm_execution_core(ctx, confirm: bool) -> str:
    """Resuelve una ejecución pendiente de Propose-Commit según la confirmación."""
    session_id = _session_key(ctx)
    state = _load_state(session_id)
    pending = state.pop("pending", None)
    if not isinstance(pending, dict) or not pending.get("goal"):
        return NO_PENDING_MESSAGE
    if not confirm:
        _save_state(session_id, state)
        return CANCELLED_MESSAGE
    goal = str(pending["goal"])
    task_id = str(uuid.uuid4())
    decision = await router.route(task_id, goal)
    if decision.action == RouteAction.BLOCK:
        _save_state(session_id, state)
        return BLOCK_MESSAGE
    if decision.action == RouteAction.FAST:
        _save_state(session_id, state)
        return await _fast_answer(task_id, goal, decision.model)
    try:
        _dispatch_orchestrator(task_id, goal)
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo despachar la tarea a Celery")
        _save_state(session_id, state)
        raise RuntimeError(f"No se pudo lanzar el equipo de subagentes: {exc}") from exc
    _set_active_in_state(state, task_id, goal)
    _save_state(session_id, state)
    return CONFIRMED_MESSAGE.format(goal=goal)


async def cancel_task_core(ctx) -> str:
    """Revoca la tarea Celery activa de la sesión y publica ``task_cancelled``."""
    session_id = _session_key(ctx)
    state = _load_state(session_id)
    active = state.pop("active", None)
    if not isinstance(active, dict) or not active.get("task_id"):
        return NO_ACTIVE_TASK_MESSAGE
    task_id = str(active["task_id"])
    goal = str(active.get("goal", ""))
    _safe_revoke(task_id)
    await _publish_task_cancelled(task_id, goal)
    _save_state(session_id, state)
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