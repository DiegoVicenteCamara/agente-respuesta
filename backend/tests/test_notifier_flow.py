"""Flujo de notificaciones de voz: filtrado por prioridad en el listener.

Cubre ``_listen_for_updates`` + ``notifier.build_spoken_update`` end-to-end con
Redis fake: ``silent`` nunca interrumpe, ``info``/``urgent`` sí con su prefacio.
"""

import asyncio
import json

import pytest

from backend.voice import agent as voice_agent


class FakePubSub:
    def __init__(self, frames) -> None:
        self._frames = frames
        self.subscribed: list[str] = []

    async def subscribe(self, channel) -> None:
        self.subscribed.append(channel)

    async def listen(self):
        for frame in self._frames:
            yield frame


class FakeRedis:
    def __init__(self, frames) -> None:
        self._frames = frames
        self.pubsub_obj = FakePubSub(frames)

    def pubsub(self):
        return self.pubsub_obj


class FakeSession:
    def __init__(self, fail_on: set[int] | None = None) -> None:
        self.replies: list[str] = []
        self.calls = 0
        self._fail_on = fail_on or set()

    async def generate_reply(self, *, instructions=None, **kwargs):
        self.calls += 1
        if self.calls in self._fail_on:
            raise RuntimeError("sala caída")
        self.replies.append(instructions)


def _msg(payload: dict) -> dict:
    return {"type": "message", "data": json.dumps(payload, ensure_ascii=False)}


def _run_listen(monkeypatch, frames, session=None):
    """Inyecta Redis fake + earcon no-op y ejecuta el listener hasta agotar."""
    session = session or FakeSession()
    earcon_calls: list[dict] = []

    async def fake_earcon(_sess, _payload):
        earcon_calls.append(_payload)
        return False

    monkeypatch.setattr(
        voice_agent.redis_client, "get_async", lambda: FakeRedis(frames)
    )
    monkeypatch.setattr(voice_agent, "play_earcon", fake_earcon)
    task = asyncio.ensure_future(voice_agent._listen_for_updates(session))
    return session, earcon_calls, task


@pytest.mark.asyncio
async def test_silent_never_interrupts(monkeypatch):
    session, earcon_calls, task = _run_listen(
        monkeypatch, [_msg({"message": "sigilo", "priority": "silent"})]
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == []
    assert earcon_calls == []


@pytest.mark.asyncio
async def test_info_interrupts_with_polite_prefix(monkeypatch):
    session, _, task = _run_listen(
        monkeypatch, [_msg({"message": "Búsqueda terminada", "priority": "info"})]
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == ["Disculpa que te interrumpa, Búsqueda terminada"]


@pytest.mark.asyncio
async def test_urgent_interrupts_with_attention_prefix(monkeypatch):
    session, _, task = _run_listen(
        monkeypatch,
        [_msg({"message": "Elige A o B", "priority": "urgent"})],
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == ["Necesito tu atención. Elige A o B"]


@pytest.mark.asyncio
async def test_default_priority_is_info(monkeypatch):
    session, _, task = _run_listen(monkeypatch, [_msg({"message": "listo"})])
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == ["Disculpa que te interrumpa, listo"]


@pytest.mark.asyncio
async def test_task_cancelled_and_empty_messages_are_silent(monkeypatch):
    session, _, task = _run_listen(
        monkeypatch,
        [
            _msg({"type": "task_cancelled", "message": "Tarea cancelada", "priority": "info"}),
            _msg({"priority": "info", "message": "   "}),
            _msg({"priority": "info"}),
            _msg({"type": "memory_recalled", "message": "recuerdo", "priority": "silent"}),
        ],
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == []


@pytest.mark.asyncio
async def test_mixed_sequence_only_speaks_audible_in_order(monkeypatch):
    session, _, task = _run_listen(
        monkeypatch,
        [
            _msg({"message": "sigilo", "priority": "silent"}),
            _msg({"message": "avance uno", "priority": "info"}),
            _msg({"message": "decide ya", "priority": "urgent"}),
            _msg({"message": "otro sigilo", "priority": "silent"}),
        ],
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == [
        "Disculpa que te interrumpa, avance uno",
        "Necesito tu atención. decide ya",
    ]


@pytest.mark.asyncio
async def test_invalid_frames_are_ignored(monkeypatch):
    session, _, task = _run_listen(
        monkeypatch,
        [
            {"type": "subscribe", "data": "ok"},  # no es "message"
            {"type": "message", "data": "{no-json"},
            {"type": "message", "data": None},
            _msg({"message": "tras el ruido", "priority": "info"}),
        ],
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == ["Disculpa que te interrumpa, tras el ruido"]


@pytest.mark.asyncio
async def test_reply_failure_does_not_kill_listener(monkeypatch):
    session = FakeSession(fail_on={1})
    session, _, task = _run_listen(
        monkeypatch,
        [
            _msg({"message": "primero", "priority": "info"}),
            _msg({"message": "segundo", "priority": "urgent"}),
        ],
        session=session,
    )
    await asyncio.wait_for(task, timeout=2)
    assert session.replies == ["Necesito tu atención. segundo"]
