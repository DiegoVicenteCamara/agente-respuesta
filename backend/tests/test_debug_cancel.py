"""Tests del endpoint POST /debug/cancel/{task_id} (issue #49)."""

import pytest
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient

from backend.api import main
from backend.bus import redis_client


@pytest.fixture
def client_with_redis(monkeypatch):
    fake = FakeAsyncRedis(decode_responses=True)

    async def _fake_client():
        return fake

    monkeypatch.setattr(redis_client, "_make_client", _fake_client)
    main.DEBUG_TASKS.clear()
    yield TestClient(main.app)
    main.DEBUG_TASKS.clear()


def _mock_celery_revoke(monkeypatch):
    import backend.orchestrator.tasks as tasks

    revoked = {}

    class FakeControl:
        @staticmethod
        def revoke(task_id, terminate=False, signal=None):
            revoked["task_id"] = task_id
            revoked["terminate"] = terminate

    class FakeApp:
        control = FakeControl()

    monkeypatch.setattr(tasks, "celery_app", FakeApp())
    return revoked


def _mock_run_pipeline(monkeypatch):
    import backend.orchestrator.tasks as tasks

    class Fake:
        @staticmethod
        def apply_async(**kwargs):
            return None

    monkeypatch.setattr(tasks, "run_pipeline", Fake())


def test_cancel_unknown_task_returns_404(client_with_redis, monkeypatch):
    _mock_celery_revoke(monkeypatch)
    resp = client_with_redis.post("/debug/cancel/web-inexistente")
    assert resp.status_code == 404


def test_cancel_revokes_and_publishes_event(client_with_redis, monkeypatch):
    revoked = _mock_celery_revoke(monkeypatch)
    _mock_run_pipeline(monkeypatch)

    run = client_with_redis.post("/debug/run", json={"goal": "tarea lenta"})
    assert run.status_code == 200
    task_id = run.json()["task_id"]

    resp = client_with_redis.post(f"/debug/cancel/{task_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == task_id
    assert body["cancelled"] is True
    assert revoked["task_id"] == task_id
    assert revoked["terminate"] is True

    # El evento task_cancelled queda en el historial y marca la tarea como done.
    detail = client_with_redis.get(f"/tasks/{task_id}")
    assert detail.status_code == 200
    events = detail.json()["events"]
    assert any(e["type"] == "task_cancelled" for e in events)

    tasks = client_with_redis.get("/tasks").json()
    item = next(t for t in tasks if t["task_id"] == task_id)
    assert item["status"] == "done"


def test_cancel_second_time_returns_404(client_with_redis, monkeypatch):
    _mock_celery_revoke(monkeypatch)
    _mock_run_pipeline(monkeypatch)

    task_id = client_with_redis.post("/debug/run", json={"goal": "otra"}).json()["task_id"]
    assert client_with_redis.post(f"/debug/cancel/{task_id}").status_code == 200
    # Ya terminada (cancelada): sin tarea en curso -> 404.
    assert client_with_redis.post(f"/debug/cancel/{task_id}").status_code == 404


def test_cancel_finished_task_returns_404(client_with_redis, monkeypatch):
    _mock_celery_revoke(monkeypatch)
    awaitable = client_with_redis
    # Tarea con analysis_ready previo (sin pasar por /debug/run).
    import asyncio

    async def _seed():
        await redis_client.publish_event(
            {
                "task_id": "web-hecha",
                "type": "analysis_ready",
                "agent": "synthesize",
                "message": "listo",
                "priority": "info",
                "ts": 1,
                "goal": "g",
            }
        )

    asyncio.run(_seed())
    assert awaitable.post("/debug/cancel/web-hecha").status_code == 404


def test_debug_run_uses_celery_task_id(monkeypatch, client_with_redis):
    import backend.orchestrator.tasks as tasks

    seen = {}

    class Fake:
        @staticmethod
        def apply_async(**kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(tasks, "run_pipeline", Fake())
    resp = client_with_redis.post("/debug/run", json={"goal": "hola"})
    task_id = resp.json()["task_id"]
    assert seen["task_id"] == task_id
    assert seen["kwargs"]["task_id"] == task_id
