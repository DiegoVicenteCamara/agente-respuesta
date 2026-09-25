"""Tests del seguimiento de coste por tarea (tokens → €)."""

import json

import pytest

from backend.config import settings
from backend.orchestrator import cost
from backend.orchestrator.cost import CostTracker, ModelUsage, TokenUsageCallback


class _Msg:
    def __init__(self, usage=None, text=""):
        self.usage_metadata = usage
        self.text = text


class _Gen:
    def __init__(self, msg=None, text=""):
        self.message = msg
        self.text = text


class _Resp:
    def __init__(self, gens, llm_output=None):
        self.generations = gens
        self.llm_output = llm_output


def test_estimate_cost_gpt_4o_mini_defaults(monkeypatch):
    monkeypatch.setattr(settings, "cost_eur_per_usd", 1.0)
    assert cost.estimate_cost_eur("gpt-4o-mini", 1_000_000, 0) == pytest.approx(0.15)
    assert cost.estimate_cost_eur("gpt-4o-mini", 0, 1_000_000) == pytest.approx(0.60)


def test_estimate_cost_applies_eur_rate(monkeypatch):
    monkeypatch.setattr(settings, "cost_eur_per_usd", 2.0)
    assert cost.estimate_cost_eur("gpt-4o-mini", 100_000, 0) == pytest.approx(0.03)


def test_estimate_cost_unknown_model_is_zero():
    assert cost.estimate_cost_eur("modelo-desconocido", 1_000_000, 1_000_000) == 0.0


def test_callback_captures_usage_metadata():
    tracker = CostTracker()
    token = cost._tracker.set(tracker)
    try:
        cb = TokenUsageCallback("gpt-4o-mini")
        cb.on_llm_end(
            _Resp([[_Gen(_Msg({"input_tokens": 10, "output_tokens": 5}))]])
        )
        assert tracker.samples == [ModelUsage("gpt-4o-mini", 10, 5)]
    finally:
        cost._tracker.reset(token)


def test_callback_captures_token_usage_fallback():
    tracker = CostTracker()
    token = cost._tracker.set(tracker)
    try:
        cb = TokenUsageCallback("gpt-4o")
        cb.on_llm_end(
            _Resp(
                [[_Gen(_Msg())]],
                llm_output={"token_usage": {"prompt_tokens": 7, "completion_tokens": 3}},
            )
        )
        assert tracker.samples == [ModelUsage("gpt-4o", 7, 3)]
    finally:
        cost._tracker.reset(token)


def test_callback_falls_back_to_tiktoken_without_metadata():
    tracker = CostTracker()
    token = cost._tracker.set(tracker)
    try:
        cb = TokenUsageCallback("gpt-4o-mini")
        cb.on_llm_start({}, ["hola mundo"])
        cb.on_llm_end(_Resp([[_Gen(_Msg(), text="una respuesta corta")]]))
        assert len(tracker.samples) == 1
        sample = tracker.samples[0]
        assert sample.tokens_in > 0
        assert sample.tokens_out > 0
    finally:
        cost._tracker.reset(token)


def test_tracker_aggregates_totals():
    tracker = CostTracker()
    tracker.add("a", 10, 5)
    tracker.add("b", 100, 50)
    tracker.add("a", 1, 1)
    assert tracker.totals() == (111, 56)


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


@pytest.mark.asyncio
async def test_publish_cost_ready_payload(fake_redis):
    async with cost.tracked() as tracker:
        tracker.add("gpt-4o-mini", 1_000_000, 0)
        await cost.publish_cost_ready("t1", "gpt-4o-mini")

    payloads = [json.loads(raw) for _, raw in fake_redis.events]
    assert len(payloads) == 1
    p = payloads[0]
    assert p["type"] == "cost_ready"
    assert p["priority"] == "silent"
    assert p["agent"] == "cost"
    assert p["task_id"] == "t1"
    assert p["model"] == "gpt-4o-mini"
    assert p["tokens_in"] == 1_000_000
    assert p["tokens_out"] == 0
    assert p["cost_eur"] == pytest.approx(0.15)
    assert p["estimated"] is True


@pytest.mark.asyncio
async def test_publish_cost_ready_disabled(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "cost_tracking_enabled", False)
    async with cost.tracked() as tracker:
        tracker.add("gpt-4o-mini", 100, 10)
        await cost.publish_cost_ready("t1", "gpt-4o-mini")
    assert fake_redis.events == []


def test_fast_task_emits_cost_ready(fake_redis, monkeypatch):
    from backend.decision.schemas import RouteAction, RouteDecision
    from backend.orchestrator import tasks

    _patch_route(
        monkeypatch,
        "backend.decision.router.route",
        RouteDecision(action=RouteAction.FAST, reason="test", model="gpt-4o-mini"),
    )

    async def fake_answer(goal: str, model: str | None = None) -> str:
        tracker = cost.current()
        assert tracker is not None
        tracker.add(model or "gpt-4o-mini", 1_000_000, 0)
        return "Respuesta rápida"

    monkeypatch.setattr("backend.decision.respond.quick_answer", fake_answer)

    assert tasks.run_pipeline("t-fast-cost", "¿Qué hora es?") == "Respuesta rápida"
    payloads = [json.loads(raw) for _, raw in fake_redis.events]
    ready = [p for p in payloads if p["type"] == "cost_ready"]
    assert len(ready) == 1
    assert ready[0]["priority"] == "silent"
    assert ready[0]["tokens_in"] == 1_000_000
    assert ready[0]["cost_eur"] > 0


def test_orchestrator_task_emits_cost_ready(fake_redis, monkeypatch):
    from backend.decision.schemas import RouteAction, RouteDecision
    from backend.orchestrator import nodes, tasks

    _patch_route(
        monkeypatch,
        "backend.decision.router.route",
        RouteDecision(action=RouteAction.ORCHESTRATOR, reason="test", model="gpt-4o"),
    )

    async def fake_chat(text: str, system: str, model: str | None = None) -> str:
        tracker = cost.current()
        assert tracker is not None
        tracker.add(model or "gpt-4o", 500_000, 0)
        return "resumen"

    monkeypatch.setattr(nodes, "chat", fake_chat)

    class _FakeGraph:
        async def ainvoke(self, initial):
            await nodes.chat("plan", "sys", model=initial.get("planner_model") or "gpt-4o")
            return {"analysis": "informe final"}

    monkeypatch.setattr("backend.orchestrator.graph.build_graph", lambda: _FakeGraph())

    assert tasks.run_pipeline("t-orch-cost", "Investiga el mercado") == "informe final"
    payloads = [json.loads(raw) for _, raw in fake_redis.events]
    ready = [p for p in payloads if p["type"] == "cost_ready"]
    assert len(ready) == 1
    assert ready[0]["model"] == "gpt-4o"
    assert ready[0]["tokens_in"] == 500_000
    assert ready[0]["estimated"] is True


def _patch_route(monkeypatch, target: str, decision):
    async def fake_route(_task_id: str, _goal: str):
        return decision

    monkeypatch.setattr(target, fake_route)
    return decision