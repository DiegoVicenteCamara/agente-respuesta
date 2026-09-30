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
    records: dict = {}

    async def fake_plan(
        goal: str, model: str | None = None, memory: str | None = None
    ) -> list[str]:
        records["goal"] = goal
        records["memory"] = memory
        return ["Subtarea A", "Subtarea B"]

    async def fake_search(query: str, max_results: int = 5) -> list[str]:
        return [f"Resultado para: {query}"]

    async def fake_chat(text: str, system: str) -> str:
        return f"Resumen de: {(text or '')[:40]}"

    monkeypatch.setattr(nodes, "plan_subtasks", fake_plan)
    monkeypatch.setattr(nodes, "run_search", fake_search)
    monkeypatch.setattr(nodes, "chat", fake_chat)
    return records


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
    assert {"plan_ready", "subtask_started", "subtask_done", "analysis_ready"} <= kinds
    assert all(p["task_id"] == "t1" for p in payloads)
    assert all(isinstance(p.get("ts"), int) for p in payloads)
    for p in payloads:
        if p["type"] in {"subtask_started", "subtask_done"}:
            assert p["subtask"] in {"Subtarea A", "Subtarea B"}


@pytest.mark.asyncio
async def test_plan_fallback_to_single_subtask(fake_redis, monkeypatch):
    from backend.orchestrator.graph import build_graph

    async def fake_subtasks(goal: str, model: str | None = None, memory: str | None = None) -> list[str]:
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


@pytest.mark.asyncio
async def test_planner_loads_memory_and_synthesize_stores_it(
    fake_redis, stub_nodes, monkeypatch
):
    from backend.orchestrator import graph

    captured: dict = {}

    async def fake_memory_load(user_id: str | None) -> str | None:
        captured["loaded_for"] = user_id
        return "resumen de la conversación anterior"

    async def fake_memory_store(user_id: str | None, goal: str, analysis: str) -> None:
        captured["stored"] = (user_id, goal, analysis)

    monkeypatch.setattr(graph, "_load_memory", fake_memory_load)
    monkeypatch.setattr(graph, "_store_memory", fake_memory_store)

    g = graph.build_graph()
    state = await g.ainvoke(
        {
            "task_id": "t3",
            "goal": "Objetivo con memoria",
            "user_id": "usuario-42",
            "results": [],
            "progress": [],
        }
    )

    assert stub_nodes["memory"] == "resumen de la conversación anterior"
    assert captured["loaded_for"] == "usuario-42"
    assert captured["stored"] == ("usuario-42", "Objetivo con memoria", state["analysis"])


@pytest.mark.asyncio
async def test_planner_skips_memory_without_user_id(fake_redis, stub_nodes, monkeypatch):
    from backend.orchestrator import graph

    async def fake_memory_load(user_id: str | None) -> str | None:
        raise AssertionError("no debe cargar memoria sin user_id")

    monkeypatch.setattr(graph, "_load_memory", fake_memory_load)

    g = graph.build_graph()
    state = await g.ainvoke(
        {"task_id": "t4", "goal": "Objetivo anónimo", "results": [], "progress": []}
    )
    assert state["analysis"].startswith("Resumen de:")
    assert stub_nodes["memory"] is None


@pytest.mark.asyncio
async def test_plan_subtasks_embeds_memory_context(fake_redis, monkeypatch):
    from backend.orchestrator import nodes

    captured: dict = {}

    async def fake_chat(text: str, system: str, model: str | None = None) -> str:
        captured["text"] = text
        return '{"subtasks": ["A"]}'

    monkeypatch.setattr(nodes, "chat", fake_chat)
    subtasks = await nodes.plan_subtasks("Investigar X", memory="el usuario ya vio Y")
    assert subtasks == ["A"]
    assert "Contexto de conversaciones previas del usuario: el usuario ya vio Y" in captured["text"]