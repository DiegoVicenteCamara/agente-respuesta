"""Tests del servicio de memoria persistente (issue #8)."""

import json

import pytest

from backend.bus import redis_client
from backend.memory import service
from backend.voice import notifier


class _FakeSyncRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.data[key] = value
        if ex is not None:
            self.ttls[key] = ex


class _FakeRedisPubSub:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    async def publish(self, channel: str, message: str) -> None:
        self.events.append((channel, message))


@pytest.fixture
def memory_redis(monkeypatch):
    fake = _FakeSyncRedis()
    monkeypatch.setattr(redis_client, "get_sync", lambda: fake)
    monkeypatch.setattr(service.settings, "memory_enabled", True)
    monkeypatch.setattr(service.settings, "memory_ttl_days", 30)
    monkeypatch.setattr(service.settings, "memory_max_chars", 2000)
    return fake


@pytest.fixture
def fake_events(monkeypatch):
    fake = _FakeRedisPubSub()

    async def fake_publish(payload: dict) -> None:
        await fake.publish("agent_updates", json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr("backend.bus.redis_client.publish_event", fake_publish)
    return fake


async def test_store_uses_user_key_with_ttl(memory_redis):
    await service.store("user-1", "resumen", ttl_days=30)
    assert memory_redis.data["user:user-1:memory"] == "resumen"
    assert memory_redis.ttls["user:user-1:memory"] == 30 * 86400


async def test_load_roundtrip(memory_redis):
    await service.store("user-1", "resumen guardado")
    assert await service.load("user-1") == "resumen guardado"


async def test_load_without_user_id_returns_none(memory_redis):
    assert await service.load(None) is None
    assert await service.load("") is None


async def test_store_and_load_disabled_are_noops(monkeypatch):
    monkeypatch.setattr(service.settings, "memory_enabled", False)
    monkeypatch.setattr(redis_client, "get_sync", lambda: _FakeSyncRedis())
    await service.store("user-1", "no debe guardarse")
    assert await service.load("user-1") is None


async def test_load_tolerates_redis_error(memory_redis, monkeypatch):
    def broken():
        raise ConnectionError("redis caído")

    monkeypatch.setattr(redis_client, "get_sync", broken)
    assert await service.load("user-1") is None


def test_mem_helpers_roundtrip_with_ttl(memory_redis):
    redis_client.mem_set("k", "v", ttl_seconds=120)
    assert redis_client.mem_get("k") == "v"
    assert memory_redis.ttls["k"] == 120


async def test_summarize_uses_llm_when_available(memory_redis, monkeypatch):
    async def fake_chat(text: str, system: str, model=None) -> str:
        assert "nuevo hallazgo" in text
        assert "previo" in text
        return "Resumen LLM del usuario"

    monkeypatch.setattr(service, "chat", fake_chat)
    assert await service.summarize("Objetivo X", "nuevo hallazgo", "previo") == "Resumen LLM del usuario"


async def test_summarize_falls_back_to_deterministic(memory_redis, monkeypatch):
    async def fake_chat(*_args, **_kwargs) -> str:
        return ""

    monkeypatch.setattr(service, "chat", fake_chat)
    summary = await service.summarize("Objetivo X", "respuesta", None)
    assert summary == "Objetivo X: respuesta"


async def test_summarize_truncates_to_max_chars(memory_redis, monkeypatch):
    monkeypatch.setattr(service.settings, "memory_max_chars", 10)

    async def fake_chat(*_args, **_kwargs) -> str:
        return ""

    monkeypatch.setattr(service, "chat", fake_chat)
    summary = await service.summarize("Objetivo X", "respuesta larga que no cabe", None)
    assert len(summary) == 10
    assert summary == summary[:10]


async def test_publish_recalled_publishes_silent_event(memory_redis, fake_events):
    await service.publish_recalled("user-1", "La última vez investigaste mercados")
    payloads = [json.loads(raw) for _, raw in fake_events.events]
    recalled = [p for p in payloads if p["type"] == "memory_recalled"]
    assert len(recalled) == 1
    event = recalled[0]
    assert event["user_id"] == "user-1"
    assert event["priority"] == "silent"
    assert isinstance(event["ts"], int)
    assert notifier.build_spoken_update(event) is None


async def test_publish_recalled_disabled_is_noop(monkeypatch, fake_events):
    monkeypatch.setattr(service.settings, "memory_enabled", False)
    await service.publish_recalled("user-1", "recuerdo")
    assert fake_events.events == []