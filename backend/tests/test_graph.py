import json

import pytest

from backend.orchestrator import nodes


class _FakeRedis:
    def __init__(self):
        self.events: list[tuple[str, str]] = []

    async def publish(self, channel: str, message: str) -> None:
        self.events.append((channel, message))


@pytest.fixture
def fake_redis(monkeypatch):
    fake = _FakeRedis()

    async def fake_publish_event(payload: dict) -> None:
        await fake.publish("agent_updates", json.dumps(payload, ensure_ascii=False))

    monkeypatch.setattr("backend.bus.redis_client.publish_event", fake_publish_event)
    return fake


@pytest.fixture
def stub_nodes(monkeypatch):
    async def fake_plan(goal: str, model: str | None = None) -> list[str]:
        return ["Subtarea A", "Subtarea B"]

    async def fake_search(query: str, max_results: int = 5) -> list[str]:
        return [f"Resultado para: {query}"]

    async def fake_chat(text: str, system: str) -> str:
        return f"Resumen de: {(text or '')[:40]}"

    monkeypatch.setattr(nodes, "plan_subtasks", fake_plan)
    monkeypatch.setattr(nodes, "run_search", fake_search)
    monkeypatch.setattr(nodes, "chat", fake_chat)


@pytest.mark.asyncio
async def test_pipeline_publishes_and_synthesizes(fake_redis, stub_nodes):
    from backend.orchestrator.graph import build_graph

    graph = build_graph()
    state = await graph.ainvoke(
        {"task_id": "t1", "goal": "¿Qué hay de nuevo?", "results": [], "progress": []}
    )

    assert state["analysis"].startswith("Resumen de:")
    assert state["results"], "debe consolidar los resultados de los subagentes"
    assert len(state["subtasks"]) == 2

    channels = {channel for channel, _ in fake_redis.events}
    assert channels == {"agent_updates"}
    payloads = [json.loads(m) for _, m in fake_redis.events]
    kinds = {p["type"] for p in payloads}
    assert {"plan_ready", "subtask_done", "analysis_ready"} <= kinds
    assert all(p["task_id"] == "t1" for p in payloads)


@pytest.mark.asyncio
async def test_plan_fallback_to_single_subtask(fake_redis, monkeypatch):
    from backend.orchestrator.graph import build_graph

    async def fake_subtasks(goal: str, model: str | None = None) -> list[str]:
        return [goal]

    monkeypatch.setattr(nodes, "plan_subtasks", fake_subtasks)
    monkeypatch.setattr(
        nodes, "run_search", lambda query, max_results=5: _async_list([f"R: {query}"])
    )
    monkeypatch.setattr(
        nodes, "chat", lambda text, system: _async_str("Informe breve")
    )

    graph = build_graph()
    state = await graph.ainvoke(
        {"task_id": "t2", "goal": "Objetivo único", "results": [], "progress": []}
    )
    assert state["analysis"] == "Informe breve"
    assert len(state["results"]) == 1


async def _async_list(items):
    return items


async def _async_str(value: str) -> str:
    return value