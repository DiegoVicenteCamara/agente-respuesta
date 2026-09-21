"""Tareas Celery: ejecución duradera del pipeline multiagente.

El worker ejecuta el grafo LangGraph en un bucle asyncio aislado; cada nodo
publica eventos a Redis que el agente de voz consume para interrumpir
proactivamente al usuario.
"""

import asyncio
import logging

from celery import Celery

from backend.config import settings

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


def _run_graph(task_id: str, goal: str) -> str:
    from backend.orchestrator.graph import build_graph

    graph = build_graph()
    initial = {"task_id": task_id, "goal": goal, "results": [], "progress": []}
    result = asyncio.run(graph.ainvoke(initial))
    return result.get("analysis", "")


@celery_app.task(name="run_pipeline")
def run_pipeline(task_id: str, goal: str) -> str:
    try:
        return _run_graph(task_id, goal)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline falló para task_id=%s", task_id)
        raise exc