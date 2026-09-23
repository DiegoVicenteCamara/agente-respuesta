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

# Historial de tareas (issue #10): persistencia ligera sobre pub/sub.
TASKS_INDEX = "tasks:index"
TASK_TTL_SECONDS = 7 * 24 * 3600
MAX_EVENTS_PER_TASK = 500
MAX_TASKS = 200


def task_events_key(task_id: str) -> str:
    return f"task:{task_id}:events"


def task_meta_key(task_id: str) -> str:
    return f"task:{task_id}:meta"


def _task_status(payload: dict[str, Any]) -> str:
    if payload.get("type") == "analysis_ready":
        return "done"
    if payload.get("type") == "blocked":
        return "blocked"
    if payload.get("priority") == "urgent":
        return "done"
    return "running"


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


async def publish_event(payload: dict[str, Any]) -> None:
    client = AsyncRedis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1.5,
        socket_timeout=1.5,
    )
    try:
        await client.publish(
            settings.event_channel, json.dumps(payload, ensure_ascii=False)
        )
    except Exception as exc:  # noqa: BLE001
        raise ConnectionError("Redis no accesible") from exc
    finally:
        # Persistencia del historial: best-effort, nunca eleva. Se hace con
        # el mismo cliente async para no abrir otra conexión; si falla, log.
        try:
            await _persist_event(client, payload)
        except Exception:  # noqa: BLE001
            logger.warning("No se pudo persistir el evento en el historial")
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass


async def _persist_event(client: AsyncRedis, payload: dict[str, Any]) -> None:
    """Guarda el evento en task:{id}:events y actualiza tasks:index + meta.

    Diseñado para llamarse desde _publish/publish_event (único punto de
    escritura): todo evento publicado queda automáticamente en el historial.
    """
    task_id = str(payload.get("task_id") or "").strip()
    if not task_id:
        return
    ts = payload.get("ts")
    try:
        ts_int = int(ts) if ts is not None else int(time.time() * 1000)
    except (TypeError, ValueError):
        ts_int = int(time.time() * 1000)
    data = json.dumps(payload, ensure_ascii=False)
    events_key = task_events_key(task_id)
    meta_key = task_meta_key(task_id)
    pipe = client.pipeline()
    pipe.rpush(events_key, data)
    pipe.ltrim(events_key, -MAX_EVENTS_PER_TASK, -1)
    pipe.expire(events_key, TASK_TTL_SECONDS)
    pipe.zadd(TASKS_INDEX, {task_id: ts_int})
    # Recorta el índice para no crecer sin cota (ligero).
    pipe.zremrangebyrank(TASKS_INDEX, 0, -(MAX_TASKS + 1))
    pipe.expire(TASKS_INDEX, TASK_TTL_SECONDS)
    await pipe.execute()
    # Meta como hash: solo actualiza último evento/estado; el goal lo fija
    # register_task (POST /debug/run) o el primer evento que lo traiga.
    try:
        meta: dict[str, Any] = {
            "task_id": task_id,
            "ts": str(ts_int),
            "last_event": str(payload.get("type") or ""),
            "status": _task_status(payload),
            "last_message": str(payload.get("message") or "")[:500],
        }
        if payload.get("goal"):
            meta["goal"] = str(payload.get("goal"))[:500]
        if payload.get("type") == "analysis_ready":
            meta["analysis"] = str(payload.get("message") or "")[:2000]
        await client.hset(meta_key, mapping=meta)  # type: ignore[arg-type]
        await client.expire(meta_key, TASK_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        logger.warning("No se pudo actualizar la meta de la tarea %s", task_id)


def register_task(task_id: str, goal: str, ts_ms: int | None = None) -> None:
    """Registra una tarea en el índice con su objetivo (tolerante a Redis caído)."""
    task_id = (task_id or "").strip()
    if not task_id:
        return
    ts_int = ts_ms if ts_ms is not None else int(time.time() * 1000)
    try:
        client = get_sync()
        client.zadd(TASKS_INDEX, {task_id: ts_int})
        client.zremrangebyrank(TASKS_INDEX, 0, -(MAX_TASKS + 1))
        client.expire(TASKS_INDEX, TASK_TTL_SECONDS)
        meta_key = task_meta_key(task_id)
        existing = client.hgetall(meta_key) or {}
        mapping = {
            "task_id": task_id,
            "goal": (goal or "")[:500],
            "ts": str(existing.get("ts") or ts_int),
            "status": str(existing.get("status") or "running"),
            "last_event": str(existing.get("last_event") or "created"),
            "last_message": str(existing.get("last_message") or ""),
        }
        if existing.get("analysis"):
            mapping["analysis"] = str(existing["analysis"])
        client.hset(meta_key, mapping=mapping)  # type: ignore[arg-type]
        client.expire(meta_key, TASK_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        logger.warning("register_task %s falló (Redis no accesible)", task_id)


def list_tasks(limit: int = 50) -> list[dict[str, Any]]:
    """Lista tareas recientes con su meta; [] si Redis falla."""
    try:
        client = get_sync()
        ids = client.zrevrange(TASKS_INDEX, 0, max(0, limit - 1))
    except Exception:  # noqa: BLE001
        logger.warning("list_tasks falló (Redis no accesible)")
        return []
    out: list[dict[str, Any]] = []
    for raw in ids or []:
        task_id = str(raw)
        try:
            meta = get_sync().hgetall(task_meta_key(task_id)) or {}
        except Exception:  # noqa: BLE001
            logger.warning("list_tasks: meta %s falló", task_id)
            continue
        try:
            ts = int(meta.get("ts") or 0)
        except (TypeError, ValueError):
            ts = 0
        out.append(
            {
                "task_id": task_id,
                "goal": str(meta.get("goal") or ""),
                "ts": ts,
                "last_event": str(meta.get("last_event") or ""),
                "status": str(meta.get("status") or "running"),
                "analysis": str(meta.get("analysis") or ""),
            }
        )
    return out


def get_task_events(task_id: str) -> list[dict[str, Any]] | None:
    """Eventos ordenados de una tarea; None si no existe; [] si Redis falla.

    Se devuelve None (no encontrado) solo cuando no hay eventos ni meta;
    ante Redis caído se devuelve [] para degradación elegante.
    """
    task_id = (task_id or "").strip()
    if not task_id:
        return None
    try:
        client = get_sync()
        raw_events = client.lrange(task_events_key(task_id), 0, -1)
        meta = client.hgetall(task_meta_key(task_id)) or {}
    except Exception:  # noqa: BLE001
        logger.warning("get_task_events %s falló (Redis no accesible)", task_id)
        return []
    events: list[dict[str, Any]] = []
    for raw in raw_events or []:
        try:
            events.append(json.loads(raw))
        except (TypeError, ValueError):
            continue
    if not events and not meta:
        return None
    return events


def mem_get(key: str) -> str | None:
    """Lee un valor con TTL; tolerante a Redis caído (None + log)."""
    try:
        value = get_sync().get(key)
    except Exception:  # noqa: BLE001
        logger.warning("mem_get %s falló (Redis no accesible)", key)
        return None
    return str(value) if value is not None else None


def mem_set(key: str, value: str, ttl_seconds: int) -> None:
    """Escribe un valor con TTL; tolerante a Redis caído (no-op + log)."""
    try:
        get_sync().set(key, value, ex=ttl_seconds)
    except Exception:  # noqa: BLE001
        logger.warning("mem_set %s falló (Redis no accesible)", key)