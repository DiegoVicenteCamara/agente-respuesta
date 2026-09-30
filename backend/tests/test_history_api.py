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
    return TestClient(main.app)


async def test_get_tasks_lists_summary(client_with_redis):
    await redis_client.publish_event(
        {
            "task_id": "web-1",
            "type": "plan_ready",
            "agent": "planner",
            "message": "He descompuesto la tarea",
            "priority": "info",
            "ts": 100,
            "goal": "Objetivo uno",
        }
    )
    await redis_client.publish_event(
        {
            "task_id": "web-1",
            "type": "analysis_ready",
            "agent": "synthesize",
            "message": "Resultado final",
            "priority": "info",
            "ts": 200,
        }
    )
    resp = client_with_redis.get("/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    item = body[0]
    assert item["task_id"] == "web-1"
    assert item["goal"] == "Objetivo uno"
    assert item["status"] == "done"
    assert item["analysis"] == "Resultado final"
    assert item["last_event"] == "analysis_ready"


async def test_get_task_detail(client_with_redis):
    await redis_client.publish_event(
        {
            "task_id": "web-2",
            "type": "plan_ready",
            "agent": "planner",
            "message": "Plan",
            "priority": "info",
            "ts": 100,
            "goal": "Objetivo dos",
        }
    )
    await redis_client.publish_event(
        {
            "task_id": "web-2",
            "type": "subtask_started",
            "agent": "research",
            "message": "Empezó",
            "priority": "silent",
            "ts": 150,
            "subtask": "S1",
        }
    )
    resp = client_with_redis.get("/tasks/web-2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "web-2"
    assert body["goal"] == "Objetivo dos"
    assert [e["type"] for e in body["events"]] == ["plan_ready", "subtask_started"]


async def test_get_task_detail_unknown_is_404(client_with_redis):
    resp = client_with_redis.get("/tasks/unknown")
    assert resp.status_code == 404


async def test_get_tasks_degrades_when_redis_down(monkeypatch):
    async def _broken_client():
        raise ConnectionError("Redis no accesible")

    monkeypatch.setattr(redis_client, "_make_client", _broken_client)
    client = TestClient(main.app)
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_task_detail_degrades_when_redis_down(monkeypatch):
    async def _broken_client():
        raise ConnectionError("Redis no accesible")

    monkeypatch.setattr(redis_client, "_make_client", _broken_client)
    client = TestClient(main.app)
    resp = client.get("/tasks/whatever")
    assert resp.status_code == 404