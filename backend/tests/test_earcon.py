"""Tests del earcon (tono previo) antes de interrupciones proactivas.

La política de ``backend/voice/notifier.py`` no cambia: estos tests solo
cubren que el tono suena para ``info``/``urgent``, nunca para ``silent``,
y que con ``EARCON_ENABLED=false`` la conducta queda intacta.
"""

import asyncio
import json

import pytest

from backend.config import Settings, settings
from backend.voice import agent as voice_agent
from backend.voice import earcon


@pytest.fixture
def enable_earcon(monkeypatch):
    monkeypatch.setattr(settings, "earcon_enabled", True)
    monkeypatch.setattr(settings, "earcon_path", "")
    yield


@pytest.fixture
def disable_earcon(monkeypatch):
    monkeypatch.setattr(settings, "earcon_enabled", False)
    yield


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("EARCON_ENABLED", raising=False)
    monkeypatch.delenv("EARCON_PATH", raising=False)
    fresh = Settings()
    assert fresh.earcon_enabled is False
    assert fresh.earcon_path == ""


def test_enabled_from_env(monkeypatch):
    monkeypatch.setenv("EARCON_ENABLED", "true")
    monkeypatch.setenv("EARCON_PATH", "/tmp/tono.wav")
    fresh = Settings()
    assert fresh.earcon_enabled is True
    assert fresh.earcon_path == "/tmp/tono.wav"


@pytest.mark.parametrize("priority", ["info", "urgent"])
def test_should_play_info_urgent_when_enabled(enable_earcon, priority):
    assert earcon.should_play({"message": "x", "priority": priority}) is True


def test_should_play_defaults_to_info(enable_earcon):
    assert earcon.should_play({"message": "x"}) is True


def test_should_play_silent_never(enable_earcon):
    assert earcon.should_play({"message": "x", "priority": "silent"}) is False


def test_should_play_disabled(disable_earcon):
    assert earcon.should_play({"message": "x", "priority": "info"}) is False
    assert earcon.should_play({"message": "x", "priority": "urgent"}) is False


@pytest.mark.asyncio
async def test_synthesize_tone_yields_audio_frames():
    frames = [f async for f in earcon.synthesize_tone()]
    assert frames, "el tono debe producir frames"
    first = frames[0]
    assert first.sample_rate == earcon.SAMPLE_RATE
    assert first.num_channels == 1
    assert first.samples_per_channel > 0
    total_samples = sum(f.samples_per_channel for f in frames)
    expected = int(earcon.SAMPLE_RATE * earcon.TONE_DURATION_MS / 1000)
    assert total_samples == expected


class FakeHandle:
    def __init__(self):
        self.playout_awaited = False

    async def wait_for_playout(self):
        self.playout_awaited = True


class FakeSession:
    def __init__(self, handle=None):
        self.say_calls = []
        self.handle = handle or FakeHandle()

    def say(self, text, *, audio=None, allow_interruptions=None, add_to_chat_ctx=None):
        self.say_calls.append(
            {
                "text": text,
                "audio": audio,
                "allow_interruptions": allow_interruptions,
                "add_to_chat_ctx": add_to_chat_ctx,
            }
        )
        return self.handle


@pytest.mark.asyncio
async def test_play_earcon_disabled_never_sounds(disable_earcon):
    session = FakeSession()
    played = await earcon.play_earcon(session, {"message": "x", "priority": "info"})
    assert played is False
    assert session.say_calls == []


@pytest.mark.asyncio
async def test_play_earcon_silent_never_sounds(enable_earcon):
    session = FakeSession()
    played = await earcon.play_earcon(
        session, {"message": "x", "priority": "silent"}
    )
    assert played is False
    assert session.say_calls == []


@pytest.mark.asyncio
async def test_play_earcon_info_uses_session_audio(enable_earcon):
    session = FakeSession()
    played = await earcon.play_earcon(session, {"message": "x", "priority": "info"})
    assert played is True
    assert len(session.say_calls) == 1
    call = session.say_calls[0]
    assert call["audio"] is not None
    assert call["allow_interruptions"] is False
    assert call["add_to_chat_ctx"] is False
    assert session.handle.playout_awaited is True
    # El audio debe ser frames reales audibles por la llamada.
    frames = [f async for f in call["audio"]]
    assert frames


@pytest.mark.asyncio
async def test_play_earcon_urgent_sounds(enable_earcon):
    session = FakeSession()
    played = await earcon.play_earcon(
        session, {"message": "elige A o B", "priority": "urgent"}
    )
    assert played is True
    assert len(session.say_calls) == 1


@pytest.mark.asyncio
async def test_play_earcon_swallows_errors(enable_earcon):
    class BrokenSession:
        def say(self, *args, **kwargs):
            raise RuntimeError("room caído")

    played = await earcon.play_earcon(
        BrokenSession(), {"message": "x", "priority": "info"}
    )
    assert played is False


# --- Integración con _listen_for_updates ---


class FakePubSub:
    def __init__(self, messages):
        self._messages = messages

    async def subscribe(self, channel):
        self.channel = channel

    async def listen(self):
        for payload in self._messages:
            yield {"type": "message", "data": json.dumps(payload)}


class FakeRedis:
    def __init__(self, messages):
        self._messages = messages

    def pubsub(self):
        return FakePubSub(self._messages)


class FakeVoiceSession:
    def __init__(self):
        self.replies = []

    async def generate_reply(self, *, instructions=None, **kwargs):
        self.replies.append(instructions)


@pytest.mark.asyncio
async def test_listen_plays_earcon_before_reply_for_info(
    monkeypatch, enable_earcon
):
    order = []

    async def ordered_play(sess, payload):
        order.append("earcon")
        return True

    async def ordered_reply(*, instructions=None, **kwargs):
        order.append("reply")

    monkeypatch.setattr(
        voice_agent.redis_client,
        "get_async",
        lambda: FakeRedis([{"message": "listo", "priority": "info"}]),
    )
    monkeypatch.setattr(voice_agent, "play_earcon", ordered_play)
    session = FakeVoiceSession()
    session.generate_reply = ordered_reply
    task = asyncio.ensure_future(voice_agent._listen_for_updates(session))
    await asyncio.sleep(0.05)
    task.cancel()
    assert order == ["earcon", "reply"]


@pytest.mark.asyncio
async def test_listen_silent_no_earcon_no_reply(monkeypatch, enable_earcon):
    played = []

    async def spy_play(sess, payload):
        played.append(payload)
        return True

    monkeypatch.setattr(
        voice_agent.redis_client,
        "get_async",
        lambda: FakeRedis([{"message": "sigilo", "priority": "silent"}]),
    )
    monkeypatch.setattr(voice_agent, "play_earcon", spy_play)
    session = FakeVoiceSession()
    task = asyncio.ensure_future(voice_agent._listen_for_updates(session))
    await asyncio.sleep(0.05)
    task.cancel()
    assert played == []
    assert session.replies == []


@pytest.mark.asyncio
async def test_listen_disabled_no_earcon_but_replies(monkeypatch, disable_earcon):
    played = []

    async def spy_play(sess, payload):
        played.append(payload)
        return await earcon.play_earcon(sess, payload)

    monkeypatch.setattr(
        voice_agent.redis_client,
        "get_async",
        lambda: FakeRedis([{"message": "listo", "priority": "info"}]),
    )
    monkeypatch.setattr(voice_agent, "play_earcon", spy_play)
    session = FakeVoiceSession()
    task = asyncio.ensure_future(voice_agent._listen_for_updates(session))
    await asyncio.sleep(0.05)
    task.cancel()
    assert played == [{"message": "listo", "priority": "info"}]
    # play_earcon real con flag off devuelve False: conducta intacta.
    assert session.replies == ["Disculpa que te interrumpa, listo"]
