import pytest
from fakeredis import FakeAsyncRedis

from backend.bus import redis_client


@pytest.fixture
def fake_redis(monkeypatch):
    client = FakeAsyncRedis(decode_responses=True)

    async def _fake_client():
        return client

    monkeypatch.setattr(redis_client, "_make_client", _fake_client)
    return client


def _event(
    task_id,
    type_,
    ts,
    message="mensaje",
    agent="research",
    priority="info",
    goal=None,
    **extra,
):
    payload = {
        "task_id": task_id,
        "type": type_,
        "agent": agent,
        "message": message,
        "priority": priority,
        "ts": ts,
    }
    payload.update(extra)
    if goal is not None:
        payload["goal"] = goal
    return payload


async def test_publish_event_persists_order_and_index(fake_redis):
    await redis_client.publish_event(_event("web-a", "plan_ready", ts=100))
    await redis_client.publish_event(_event("web-a", "subtask_started", ts=200))

    stored = await fake_redis.lrange("task:web-a:events", 0, -1)
    assert len(stored) == 2
    first = json_to_dict(stored[0])
    assert first["type"] == "plan_ready"
    assert await fake_redis.zscore("tasks:index", "web-a") == 100.0


def json_to_dict(raw: str):
    import json

    return json.loads(raw)


async def test_publish_event_records_goal_in_meta(fake_redis):
    await redis_client.publish_event(
        _event("web-a", "plan_ready", ts=100, goal="Explica Redis")
    )
    assert await fake_redis.hget("task:web-a:meta", "goal") == "Explica Redis"


async def test_index_keeps_creation_timestamp(fake_redis):
    await redis_client.publish_event(_event("web-a", "plan_ready", ts=100, goal="G"))
    await redis_client.publish_event(_event("web-a", "analysis_ready", ts=900, goal="G"))
    assert await fake_redis.zscore("tasks:index", "web-a") == 100.0


async def test_event_without_ts_is_still_stored(fake_redis):
    payload = {
        "task_id": "web-e",
        "type": "analysis_ready",
        "agent": "jev-gate",
        "message": "Respuesta rápida",
        "priority": "info",
        "goal": "Pregunta simple",
    }
    await redis_client.publish_event(payload)
    item = (await redis_client.list_tasks())[0]
    assert item["status"] == "done"
    assert item["analysis"] == "Respuesta rápida"
    assert item["goal"] == "Pregunta simple"


async def test_list_tasks_completed_task_summary(fake_redis):
    await redis_client.publish_event(_event("web-b", "plan_ready", ts=100, goal="Objetivo B"))
    await redis_client.publish_event(
        _event("web-b", "subtask_started", ts=200, priority="silent", subtask="S")
    )
    await redis_client.publish_event(
        _event("web-b", "analysis_ready", ts=300, message="Informe final")
    )

    tasks = await redis_client.list_tasks()
    assert len(tasks) == 1
    item = tasks[0]
    assert item["task_id"] == "web-b"
    assert item["goal"] == "Objetivo B"
    assert item["ts"] == 100
    assert item["last_event"] == "analysis_ready"
    assert item["status"] == "done"
    assert item["analysis"] == "Informe final"


async def test_list_tasks_orders_newest_first_and_in_progress(fake_redis):
    await redis_client.publish_event(_event("web-old", "plan_ready", ts=100, goal="Antigua"))
    await redis_client.publish_event(
        _event("web-new", "plan_ready", ts=500, goal="Reciente")
    )
    await redis_client.publish_event(
        _event("web-new", "subtask_started", ts=600, priority="silent", subtask="S")
    )

    tasks = await redis_client.list_tasks()
    assert [t["task_id"] for t in tasks] == ["web-new", "web-old"]
    new = tasks[0]
    assert new["status"] == "in_progress"
    assert new["analysis"] is None
    assert new["last_event"] == "subtask_started"


async def test_blocked_task_is_done_with_block_message(fake_redis):
    await redis_client.publish_event(
        _event("web-x", "blocked", ts=100, message="No puedo ejecutar eso", goal="Hack")
    )
    item = (await redis_client.list_tasks())[0]
    assert item["status"] == "done"
    assert item["analysis"] == "No puedo ejecutar eso"


async def test_cost_ready_keeps_task_done_after_analysis(fake_redis):
    await redis_client.publish_event(_event("web-c", "plan_ready", ts=100, goal="G"))
    await redis_client.publish_event(
        _event("web-c", "analysis_ready", ts=200, message="Análisis", agent="synthesize")
    )
    await redis_client.publish_event(
        _event(
            "web-c",
            "cost_ready",
            ts=250,
            message="Coste estimado",
            agent="cost",
            priority="silent",
        )
    )
    item = (await redis_client.list_tasks())[0]
    assert item["status"] == "done"
    assert item["last_event"] == "cost_ready"
    assert item["analysis"] == "Análisis"


async def test_get_task_events_returns_ordered_payloads(fake_redis):
    await redis_client.publish_event(_event("web-d", "plan_ready", ts=100, goal="G"))
    await redis_client.publish_event(
        _event("web-d", "subtask_started", ts=150, subtask="S1", priority="silent")
    )
    await redis_client.publish_event(
        _event("web-d", "analysis_ready", ts=200, message="Final")
    )

    detail = await redis_client.get_task_events("web-d")
    assert detail["goal"] == "G"
    assert [e["type"] for e in detail["events"]] == [
        "plan_ready",
        "subtask_started",
        "analysis_ready",
    ]
    assert detail["events"][-1]["message"] == "Final"
    assert detail["events"][0]["ts"] == 100


async def test_get_task_events_unknown_returns_empty(fake_redis):
    detail = await redis_client.get_task_events("no-existe")
    assert detail["events"] == []
    assert detail["goal"] is None