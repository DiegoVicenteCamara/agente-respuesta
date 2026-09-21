import json
from typing import Any

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from backend.config import settings

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