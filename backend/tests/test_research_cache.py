"""Tests de la caché de investigación en Redis (Tavily/DuckDuckGo)."""

import json

import pytest

from backend.bus import redis_client
from backend.config import settings
from backend.orchestrator import nodes


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


@pytest.fixture
def cache_redis(monkeypatch):
    fake = _FakeSyncRedis()
    monkeypatch.setattr(redis_client, "get_sync", lambda: fake)
    return fake


def test_cache_ttl_seconds_default():
    assert settings.cache_ttl_seconds == 86400


def test_research_hash_normalizes(cache_redis):
    assert nodes._research_hash("  Hola Mundo ") == nodes._research_hash("hola mundo")
    assert nodes._research_hash("Hola") != nodes._research_hash("Adios")


def test_research_cache_helpers_roundtrip_with_ttl(cache_redis):
    redis_client.research_cache_set("abc123", ["r1", "r2"], ttl=3600)
    assert redis_client.research_cache_get("abc123") == ["r1", "r2"]
    assert cache_redis.ttls["research:abc123"] == 3600


def test_research_cache_set_uses_config_ttl_by_default(cache_redis, monkeypatch):
    monkeypatch.setattr(settings, "cache_ttl_seconds", 999)
    redis_client.research_cache_set("h", ["x"])
    assert cache_redis.ttls["research:h"] == 999


def test_research_cache_get_miss_returns_none(cache_redis):
    assert redis_client.research_cache_get("missing") is None


def test_research_cache_get_invalid_json_returns_none(cache_redis):
    cache_redis.data["research:bad"] = "no-json{{{"
    assert redis_client.research_cache_get("bad") is None


def test_research_cache_helpers_tolerate_redis_down(monkeypatch):
    def broken():
        raise ConnectionError("redis caído")

    monkeypatch.setattr(redis_client, "get_sync", broken)
    assert redis_client.research_cache_get("any") is None
    # no debe lanzar
    redis_client.research_cache_set("any", ["r"], ttl=60)


@pytest.mark.asyncio
async def test_run_search_second_call_hits_cache(cache_redis, monkeypatch):
    calls = {"n": 0}

    async def fake_fetch(query: str, max_results: int = 5) -> list[str]:
        calls["n"] += 1
        return [f"Resultado para: {query}"]

    monkeypatch.setattr(nodes, "_fetch_search", fake_fetch)

    first = await nodes.run_search("  Mercado Laboral ")
    second = await nodes.run_search("mercado laboral")

    assert first == ["Resultado para:   Mercado Laboral "]
    assert second == first
    assert calls["n"] == 1, "la segunda búsqueda idéntica debe usar caché"


@pytest.mark.asyncio
async def test_run_search_miss_calls_provider_and_stores(cache_redis, monkeypatch):
    monkeypatch.setattr(settings, "cache_ttl_seconds", 1234)

    async def fake_fetch(query: str, max_results: int = 5) -> list[str]:
        return ["A", "B"]

    monkeypatch.setattr(nodes, "_fetch_search", fake_fetch)

    results = await nodes.run_search("Nueva consulta")
    assert results == ["A", "B"]
    cache_hash = nodes._research_hash("Nueva consulta")
    assert json.loads(cache_redis.data[f"research:{cache_hash}"]) == ["A", "B"]
    assert cache_redis.ttls[f"research:{cache_hash}"] == 1234


@pytest.mark.asyncio
async def test_run_search_degrades_when_redis_down(monkeypatch):
    def broken():
        raise ConnectionError("redis caído")

    monkeypatch.setattr(redis_client, "get_sync", broken)

    async def fake_fetch(query: str, max_results: int = 5) -> list[str]:
        return ["directo"]

    monkeypatch.setattr(nodes, "_fetch_search", fake_fetch)

    assert await nodes.run_search("cualquier tema") == ["directo"]
