"""Historial de tareas (#10): persistencia Redis + endpoints GET /tasks."""

import json

import pytest
from fastapi.testclient import TestClient

from backend.api import main
from backend.bus import redis_client


class FakeSync:
    def __init__(self):
        self.lists: dict[str, list[str]] = {}
        self.zsets: dict[str, dict[str, float]] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.fail = False

    def _check(self):
        if self.fail:
            raise ConnectionError("Redis caído")

    # listas
    def rpush(self, key, value):
        self._check()
        self.lists.setdefault(key, []).append(value)

    def ltrim(self, key, start, end):
        self._check()
        vals = self.lists.get(key, [])
        # Soporta solo el caso usado: ltrim(key, -N, -1)
        if start < 0:
            self.lists[key] = vals[start:]
        else:
            self.lists[key] = vals[start : end + 1 if end >= 0 else len(vals)]

    def lrange(self, key, start, end):
        self._check()
        vals = self.lists.get(key, [])
        if end == -1:
            return vals[start:]
        return vals[start : end + 1]

    # zset
    def zadd(self, key, mapping):
        self._check()
        self.zsets.setdefault(key, {}).update({k: float(v) for k, v in mapping.items()})

    def zremrangebyrank(self, key, start, end):
        self._check()
        ordered = sorted(self.zsets.get(key, {}).items(), key=lambda kv: kv[1])
        n = len(ordered)
        # normaliza índices negativos como Redis
        if start < 0:
            start = n + start
        if end < 0:
            end = n + end
        start = max(0, start)
        end = min(n - 1, end)
        if end >= start:
            for member, _ in ordered[start : end + 1]:
                self.zsets[key].pop(member, None)

    def zrevrange(self, key, start, end):
        self._check()
        ordered = sorted(self.zsets.get(key, {}).items(), key=lambda kv: kv[1], reverse=True)
        members = [m for m, _ in ordered]
        if end < 0:
            return members[start:]
        return members[start : end + 1]

    # hash
    def hset(self, key, mapping=None, **kwargs):
        self._check()
        data = dict(mapping or {}) | kwargs
        self.hashes.setdefault(key, {}).update({k: str(v) for k, v in data.items()})

    def hgetall(self, key):
        self._check()
        return dict(self.hashes.get(key, {}))

    def expire(self, key, ttl):
        self._check()
        return True


class FakePipeline:
    def __init__(self, fake: "FakeAsync"):
        self.fake = fake
        self.ops: list[tuple] = []

    def rpush(self, key, value):
        self.ops.append(("rpush", key, value))
        return self

    def ltrim(self, key, a, b):
        self.ops.append(("ltrim", key, a, b))
        return self

    def expire(self, key, ttl):
        self.ops.append(("expire", key, ttl))
        return self

    def zadd(self, key, mapping):
        self.ops.append(("zadd", key, mapping))
        return self

    def zremrangebyrank(self, key, a, b):
        self.ops.append(("zremrangebyrank", key, a, b))
        return self

    async def execute(self):
        for op in self.ops:
            kind = op[0]
            if kind == "rpush":
                _, key, value = op
                self.fake.lists.setdefault(key, []).append(value)
            elif kind == "ltrim":
                _, key, a, _b = op
                vals = self.fake.lists.get(key, [])
                self.fake.lists[key] = vals[a:] if a < 0 else vals[a:]
            elif kind == "zadd":
                _, key, mapping = op
                self.fake.zsets.setdefault(key, {}).update(mapping)
            elif kind == "zremrangebyrank":
                pass  # recorte no crítico en tests
            elif kind == "expire":
                pass
        return []


class FakeAsync:
    def __init__(self):
        self.published: list[tuple[str, str]] = []
        self.lists: dict[str, list[str]] = {}
        self.zsets: dict[str, dict[str, float]] = {}
        self.hashes: dict[str, dict[str, str]] = {}

    async def publish(self, channel, message):
        self.published.append((channel, message))

    def pipeline(self):
        return FakePipeline(self)

    async def hset(self, key, mapping=None, **kwargs):
        data = dict(mapping or {}) | kwargs
        self.hashes.setdefault(key, {}).update({k: str(v) for k, v in data.items()})

    async def expire(self, key, ttl):
        return True

    async def aclose(self):
        return None


@pytest.fixture
def fake_sync(monkeypatch):
    fake = FakeSync()
    monkeypatch.setattr(redis_client, "get_sync", lambda: fake)
    return fake


def test_register_list_and_detail(fake_sync):
    redis_client.register_task("t-1", "Investigar Redis", ts_ms=1000)
    assert fake_sync.hashes["task:t-1:meta"]["goal"] == "Investigar Redis"

    # Simula eventos persistidos vía sync (misma forma que _persist_event).
    fake_sync.rpush("task:t-1:events", json.dumps({"task_id": "t-1", "type": "plan_ready"}))
    fake_sync.hset(
        "task:t-1:meta",
        mapping={"last_event": "analysis_ready", "status": "done", "analysis": "Informe final"},
    )
    tasks = redis_client.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "t-1"
    assert tasks[0]["goal"] == "Investigar Redis"
    assert tasks[0]["status"] == "done"

    events = redis_client.get_task_events("t-1")
    assert events is not None and len(events) == 1
    assert events[0]["type"] == "plan_ready"


def test_get_task_events_missing_returns_none(fake_sync):
    assert redis_client.get_task_events("desconocida") is None


def test_list_tasks_redis_down_returns_empty(monkeypatch):
    fake = FakeSync()
    fake.fail = True
    monkeypatch.setattr(redis_client, "get_sync", lambda: fake)
    assert redis_client.list_tasks() == []
    assert redis_client.get_task_events("t-1") == []


def test_status_derivation():
    assert redis_client._task_status({"type": "analysis_ready"}) == "done"
    assert redis_client._task_status({"type": "blocked"}) == "blocked"
    assert redis_client._task_status({"type": "x", "priority": "urgent"}) == "done"
    assert redis_client._task_status({"type": "plan_ready"}) == "running"


@pytest.mark.asyncio
async def test_publish_event_persists_history(monkeypatch):
    fake = FakeAsync()
    monkeypatch.setattr(
        "backend.bus.redis_client.AsyncRedis.from_url", lambda *a, **k: fake
    )
    payload = {
        "task_id": "t-pub",
        "type": "analysis_ready",
        "agent": "synthesize",
        "message": "Listo",
        "priority": "info",
        "ts": 1234,
    }
    await redis_client.publish_event(payload)
    # pub/sub intacto
    assert len(fake.published) == 1
    # historial persistido con el mismo cliente
    assert "task:t-pub:events" in fake.lists
    stored = json.loads(fake.lists["task:t-pub:events"][0])
    assert stored["task_id"] == "t-pub"
    assert fake.zsets["tasks:index"]["t-pub"] == 1234
    assert fake.hashes["task:t-pub:meta"]["status"] == "done"
    assert fake.hashes["task:t-pub:meta"]["analysis"] == "Listo"


def test_api_tasks_list_and_detail(fake_sync):
    redis_client.register_task("web-abc", "Probar historial", ts_ms=2000)
    fake_sync.rpush(
        "task:web-abc:events",
        json.dumps({"task_id": "web-abc", "type": "plan_ready", "message": "hola"}),
    )
    client = TestClient(main.app)
    resp = client.get("/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert any(t["task_id"] == "web-abc" for t in body)

    resp2 = client.get("/tasks/web-abc")
    assert resp2.status_code == 200
    assert resp2.json()["events"][0]["type"] == "plan_ready"

    resp404 = client.get("/tasks/no-existe")
    assert resp404.status_code == 404


def test_api_tasks_degrades_when_redis_down(monkeypatch):
    fake = FakeSync()
    fake.fail = True
    monkeypatch.setattr(redis_client, "get_sync", lambda: fake)
    client = TestClient(main.app)
    assert client.get("/tasks").json() == []
    # Detalle ante Redis caído: degradación elegante (lista vacía, no 404).
    resp = client.get("/tasks/cualquiera")
    assert resp.status_code == 200
    assert resp.json()["events"] == []


def test_debug_run_registers_task(monkeypatch, fake_sync):
    import backend.orchestrator.tasks as tasks

    class Fake:
        @staticmethod
        def delay(**kwargs):
            pass

    monkeypatch.setattr(tasks, "run_pipeline", Fake())
    client = TestClient(main.app)
    resp = client.post("/debug/run", json={"goal": "ver historial"})
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    assert fake_sync.hashes[f"task:{task_id}:meta"]["goal"] == "ver historial"


def test_index_includes_history_panel():
    client = TestClient(main.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Historial" in resp.text
    assert 'fetch("/tasks")' in resp.text or "fetch('/tasks')" in resp.text or '/tasks' in resp.text
