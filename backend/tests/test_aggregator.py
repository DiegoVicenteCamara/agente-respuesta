"""Agregación de interrupciones proactivas en ráfaga (issue #47).

Cubre ``backend/voice/aggregator.py`` (puro) y ``_listen_for_updates``
(ventana de agregación + prioridad urgent + silent + earcon único).
"""

import asyncio
import json

import pytest

from backend.voice import agent as voice_agent
from backend.voice.aggregator import UpdateAggregator, combine_infos


# --- combine_infos / UpdateAggregator (puro) ---


def test_combine_single_info_keeps_polite_prefix():
    assert combine_infos(["Búsqueda terminada"]) == (
        "Disculpa que te interrumpa, Búsqueda terminada"
    )


def test_combine_three_infos_mentions_all():
    out = combine_infos(["uno", "dos", "tres"])
    assert out is not None
    assert "3 avances" in out
    assert "uno" in out and "dos" in out and "tres" in out


def test_combine_empty_returns_none():
    assert combine_infos([]) is None
    assert combine_infos(["   "]) is None


def test_aggregator_buffers_info_until_flush():
    agg = UpdateAggregator()
    assert agg.add({"message": "a", "priority": "info"}) == []
    assert agg.add({"message": "b", "priority": "info"}) == []
    assert agg.pending_count == 2
    out = agg.flush()
    assert out is not None
    assert "2 avances" in out and "a" in out and "b" in out
    assert agg.pending_count == 0
    assert agg.flush() is None


def test_aggregator_silent_never_buffers():
    agg = UpdateAggregator()
    assert agg.add({"message": "x", "priority": "silent"}) == []
    assert agg.add({"type": "task_cancelled", "message": "y", "priority": "info"}) == []
    assert agg.add({"priority": "info", "message": "   "}) == []
    assert agg.pending_count == 0
    assert agg.flush() is None


def test_aggregator_urgent_flushes_pending_urgent_first():
    agg = UpdateAggregator()
    assert agg.add({"message": "avance 1", "priority": "info"}) == []
    assert agg.add({"message": "avance 2", "priority": "info"}) == []
    texts = agg.add({"message": "decide ya", "priority": "urgent"})
    assert len(texts) == 2
    assert texts[0] == "Necesito tu atención. decide ya"
    assert "avance 1" in texts[1] and "avance 2" in texts[1]
    assert agg.pending_count == 0


def test_aggregator_urgent_alone_returns_single():
    agg = UpdateAggregator()
    texts = agg.add({"message": "corre", "priority": "urgent"})
    assert texts == ["Necesito tu atención. corre"]


# --- listener con ventana ---


class FakePubSub:
    def __init__(self, frames) -> None:
        self._frames = frames

    async def subscribe(self, channel) -> None:
        pass

    async def listen(self):
        for frame in self._frames:
            yield frame


class DelayedPubSub(FakePubSub):
    """Yield con pausas (delay, frame) para probar el flush por timeout."""

    async def listen(self):
        for delay, frame in self._frames:
            if delay:
                await asyncio.sleep(delay)
            yield frame


class FakeRedis:
    def __init__(self, pubsub) -> None:
        self._pubsub = pubsub

    def pubsub(self):
        return self._pubsub


class FakeSession:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def generate_reply(self, *, instructions=None, **kwargs):
        self.replies.append(instructions)


def _msg(payload: dict) -> dict:
    return {"type": "message", "data": json.dumps(payload, ensure_ascii=False)}


def _patch(monkeypatch, pubsub, earcon_calls=None):
    async def fake_earcon(_sess, _payload):
        if earcon_calls is not None:
            earcon_calls.append(_payload)
        return False

    monkeypatch.setattr(voice_agent.redis_client, "get_async", lambda: FakeRedis(pubsub))
    monkeypatch.setattr(voice_agent, "play_earcon", fake_earcon)


@pytest.mark.asyncio
async def test_three_infos_in_burst_produce_single_reply(monkeypatch):
    """3 subtask_done info con <2 s de diferencia -> 1 sola generate_reply."""
    session = FakeSession()
    earcon_calls: list[dict] = []
    frames = [
        _msg({"message": "avance uno", "priority": "info"}),
        _msg({"message": "avance dos", "priority": "info"}),
        _msg({"message": "avance tres", "priority": "info"}),
    ]
    _patch(monkeypatch, FakePubSub(frames), earcon_calls)
    await asyncio.wait_for(voice_agent._listen_for_updates(session), timeout=2)
    assert len(session.replies) == 1
    text = session.replies[0]
    assert "3 avances" in text
    assert "avance uno" in text and "avance dos" in text and "avance tres" in text
    # Earcon una sola vez por intervención agrupada.
    assert len(earcon_calls) == 1


@pytest.mark.asyncio
async def test_urgent_interrupts_with_pending_batch_not_lost(monkeypatch):
    session = FakeSession()
    _patch(monkeypatch, FakePubSub([
        _msg({"message": "avance uno", "priority": "info"}),
        _msg({"message": "decide ya", "priority": "urgent"}),
    ]))
    await asyncio.wait_for(voice_agent._listen_for_updates(session), timeout=2)
    assert session.replies[0] == "Necesito tu atención. decide ya"
    assert "avance uno" in session.replies[1]
    assert len(session.replies) == 2


@pytest.mark.asyncio
async def test_silent_never_speaks_with_open_batch(monkeypatch):
    session = FakeSession()
    _patch(monkeypatch, FakePubSub([
        _msg({"message": "avance uno", "priority": "info"}),
        _msg({"message": "sigilo", "priority": "silent"}),
        _msg({"message": "avance dos", "priority": "info"}),
    ]))
    await asyncio.wait_for(voice_agent._listen_for_updates(session), timeout=2)
    assert len(session.replies) == 1
    assert "sigilo" not in session.replies[0]
    assert "avance uno" in session.replies[0] and "avance dos" in session.replies[0]


@pytest.mark.asyncio
async def test_flush_by_timeout_splits_batches(monkeypatch):
    """Dos infos separados por más que la ventana -> 2 intervenciones."""
    session = FakeSession()
    _patch(monkeypatch, DelayedPubSub([
        (0, _msg({"message": "primero", "priority": "info"})),
        (0.12, _msg({"message": "segundo", "priority": "info"})),
    ]))
    await asyncio.wait_for(
        voice_agent._listen_for_updates(session, window_ms=50), timeout=2
    )
    assert session.replies == [
        "Disculpa que te interrumpa, primero",
        "Disculpa que te interrumpa, segundo",
    ]


def test_notify_aggr_window_default_ms(monkeypatch):
    from backend.config import Settings

    monkeypatch.delenv("NOTIFY_AGGR_WINDOW_MS", raising=False)
    assert Settings().notify_aggr_window_ms == 2500
    monkeypatch.setenv("NOTIFY_AGGR_WINDOW_MS", "1000")
    assert Settings().notify_aggr_window_ms == 1000
