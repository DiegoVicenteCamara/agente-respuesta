"""Tareas Celery: ejecución duradera del pipeline multiagente.

El worker ejecuta el grafo LangGraph en un bucle asyncio aislado; cada nodo
publica eventos a Redis que el agente de voz consume para interrumpir
proactivamente al usuario.

Defensa en profundidad: al entrar, cada tarea vuelve a pasar por el triaje
Sistema 1 (Jev). Si la tarea resultó trivial, se responde con el modelo
económico sin construir el grafo; en caso contrario el planner usa el modelo
seleccionado por la política (avanzado si el tier exige razonamiento).
"""

import asyncio
import logging

from celery import Celery

from backend.config import settings
from backend.decision import respond, router
from backend.decision.schemas import RouteAction
from backend.orchestrator import cost

logger = logging.getLogger(__name__)

celery_app = Celery(
    "agente_respuesta", broker=settings.redis_url, backend=settings.redis_url
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


async def _publish(payload: dict) -> None:
    from backend.bus import redis_client

    try:
        await redis_client.publish_event(payload)
    except ConnectionError:
        logger.warning("Redis no disponible; el evento no se publicó")
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo publicar el evento en Redis")


def _run_graph(task_id: str, goal: str, planner_model: str | None) -> str:
    from backend.orchestrator.graph import build_graph

    async def _inner() -> str:
        model = planner_model or settings.openai_planner_model
        async with cost.tracked():
            graph = build_graph()
            initial = {
                "task_id": task_id,
                "goal": goal,
                "results": [],
                "progress": [],
                "planner_model": planner_model or "",
            }
            result = await graph.ainvoke(initial)
            await cost.publish_cost_ready(task_id, model)
            return result.get("analysis", "")

    return asyncio.run(_inner())


def _handle_fast(task_id: str, goal: str, model: str) -> str:
    async def _inner() -> str:
        async with cost.tracked():
            answer = await respond.quick_answer(goal, model=model)
            await _publish(
                {
                    "task_id": task_id,
                    "type": "analysis_ready",
                    "agent": "jev-gate",
                    "message": answer,
                    "priority": "info",
                }
            )
            await cost.publish_cost_ready(task_id, model)
            return answer

    return asyncio.run(_inner())


def _handle_blocked(task_id: str) -> str:
    message = (
        "No puedo ejecutar esa solicitud: parece contener intentos de manipular "
        "mis instrucciones. Reformúlala de otra forma por favor."
    )
    asyncio.run(
        _publish(
            {
                "task_id": task_id,
                "type": "blocked",
                "agent": "jev-gate",
                "message": message,
                "priority": "info",
            }
        )
    )
    return ""


@celery_app.task(name="run_pipeline")
def run_pipeline(task_id: str, goal: str, user_id: str | None = None) -> str:
    try:
        decision = asyncio.run(router.route(task_id, goal))
        if decision.action == RouteAction.FAST:
            return _handle_fast(task_id, goal, decision.model)
        if decision.action == RouteAction.BLOCK:
            return _handle_blocked(task_id)
        # PROPOSE_COMMIT llega aquí ya confirmado (voz) o directo (debug): se
        # escala al orquestador con el modelo que fijó la política.
        return _run_graph(task_id, goal, decision.model)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline falló para task_id=%s", task_id)
        raise exc