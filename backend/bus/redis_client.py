import json
import logging
from typing import Any

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from backend.config import settings

logger = logging.getLogger(__name__)

_async: AsyncRedis | None = None
_sync: SyncRedis | None = None


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
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            pass


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


SESSION_KEY_PREFIX = "voice:"
SESSION_KEY_SUFFIX = ":state"
SESSION_TTL_SECONDS = 3600


def _session_redis_key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}{SESSION_KEY_SUFFIX}"


def session_get(session_id: str) -> dict | None:
    """Lee el estado de sesión de voz; tolerante a Redis caído (None + log)."""
    try:
        raw = get_sync().get(_session_redis_key(session_id))
    except Exception:  # noqa: BLE001
        logger.warning("session_get %s falló (Redis no accesible)", session_id)
        return None
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("session_get %s devolvió JSON inválido", session_id)
        return None
    return data if isinstance(data, dict) else None


def session_set(session_id: str, data: dict, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
    """Escribe el estado de sesión con TTL; tolerante a Redis caído (no-op + log)."""
    try:
        get_sync().set(
            _session_redis_key(session_id),
            json.dumps(data, ensure_ascii=False),
            ex=ttl_seconds,
        )
    except Exception:  # noqa: BLE001
        logger.warning("session_set %s falló (Redis no accesible)", session_id)


def session_delete(session_id: str) -> None:
    """Borra la clave de sesión; tolerante a Redis caído (no-op + log)."""
    try:
        get_sync().delete(_session_redis_key(session_id))
    except Exception:  # noqa: BLE001
        logger.warning("session_delete %s falló (Redis no accesible)", session_id)