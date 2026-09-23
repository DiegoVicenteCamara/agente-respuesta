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