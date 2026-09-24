import json
import logging
import time
from typing import Any

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from backend.config import settings

logger = logging.getLogger(__name__)

_async: AsyncRedis | None = None
_sync: SyncRedis | None = None

TERMINAL_TYPES = {"analysis_ready", "blocked"}


def get_async() -> AsyncRedis:
    global _async
    if _async is None:
        _async = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    return _async


def get_sync() -> SyncRedis:
    global _sync
    if _sync is None:
        _sync = SyncRedis.from_url(settings.redis_url, decode_responses=True)
    return _sync


async def _make_client() -> AsyncRedis:
    return AsyncRedis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1.5,
        socket_timeout=1.5,
    )


def _summarize(events: list[dict]) -> tuple[str, str | None]:
    """Deriva estado y análisis final a partir de los eventos de una tarea."""
    finished = any(
        e.get("priority") == "urgent" or e.get("type") in TERMINAL_TYPES
        for e in events
    )
    status = "done" if finished else "in_progress"
    analysis = next(
        (
            e["message"]
            for e in reversed(events)
            if e.get("type") in TERMINAL_TYPES and e.get("message")
        ),
        None,
    )
    return status, analysis


async def store_event(client: AsyncRedis, payload: dict[str, Any]) -> None:
    """Persistencia ligera del evento en la lista de la tarea y en el índice."""
    task_id = payload["task_id"]
    ts = int(payload.get("ts") or time.time() * 1000)
    await client.rpush(
        f"task:{task_id}:events", json.dumps(payload, ensure_ascii=False)
    )
    await client.zadd("tasks:index", {task_id: ts}, nx=True)
    goal = payload.get("goal")
    if goal:
        await client.hset(f"task:{task_id}:meta", "goal", goal)


async def list_tasks() -> list[dict]:
    """Tareas en el historial, de creación más reciente a más antigua."""
    client = await _make_client()
    try:
        entries = await client.zrevrange("tasks:index", 0, -1, withscores=True)
        tasks = []
        for task_id, ts in entries:
            events = [
                json.loads(raw)
                for raw in await client.lrange(f"task:{task_id}:events", 0, -1)
            ]
            status, analysis = _summarize(events)
            goal = await client.hget(f"task:{task_id}:meta", "goal")
            tasks.append(
                {
                    "task_id": task_id,
                    "goal": goal,
                    "ts": int(ts),
                    "last_event": events[-1]["type"] if events else None,
                    "status": status,
                    "analysis": analysis,
                }
            )
        return tasks
    finally:
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass


async def get_task_events(task_id: str) -> dict:
    """Eventos ordenados de una tarea (vacío si la tarea no existe)."""
    client = await _make_client()
    try:
        events = [
            json.loads(raw)
            for raw in await client.lrange(f"task:{task_id}:events", 0, -1)
        ]
        goal = await client.hget(f"task:{task_id}:meta", "goal")
        return {"goal": goal, "events": events}
    finally:
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass


async def publish_event(payload: dict[str, Any]) -> None:
    client = await _make_client()
    try:
        await client.publish(
            settings.event_channel, json.dumps(payload, ensure_ascii=False)
        )
        try:
            await store_event(client, payload)
        except Exception:  # noqa: BLE001
            logger.warning("No se pudo persistir el evento en el historial")
    except Exception as exc:  # noqa: BLE001
        raise ConnectionError("Redis no accesible") from exc
    finally:
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass