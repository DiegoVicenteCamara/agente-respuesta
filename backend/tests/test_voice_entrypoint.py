"""Integración del entrypoint de voz: identidad, memoria, bienvenida y listener.

Cubre ``backend/voice/agent.py`` (``voice_entrypoint``, ``_resolve_user_id``,
``build_welcome_instructions``) con fakes ligeros: sin LiveKit real ni Redis.
"""

import asyncio

import pytest

from backend.voice import agent as voice_agent
from backend.voice.agent import (
    WELCOME_INSTRUCTIONS,
    _resolve_user_id,
    build_welcome_instructions,
    voice_entrypoint,
)
from backend.voice import tools


class FakeParticipant:
    def __init__(self, identity: str | None) -> None:
        self.identity = identity


class FakeRoom:
    def __init__(self, participants: dict | None = None) -> None:
        self.remote_participants = participants or {}


class FakeClaims:
    def __init__(self, identity: str | None = None) -> None:
        self.identity = identity


class FakeCtx:
    """Imita lo que usa el entrypoint: room + token_claims()."""

    def __init__(self, room=None, claims=None) -> None:
        self.room = room or FakeRoom()
        self._claims = claims

    def token_claims(self):
        return self._claims


class FakeSession:
    def __init__(self) -> None:
        self.started: list[dict] = []
        self.replies: list[str] = []
        self.kwargs: list[dict] = []

    async def start(self, *, room=None, agent=None) -> None:
        self.started.append({"room": room, "agent": agent})

    async def generate_reply(self, *, instructions=None, **kwargs) -> None:
        self.replies.append(instructions)
        self.kwargs.append(kwargs)


class FakeAgent:
    pass


@pytest.fixture(autouse=True)
def _reset_user_id():
    token = tools.USER_ID.set(None)
    try:
        yield
    finally:
        tools.USER_ID.reset(token)


def _entrypoint_harness(monkeypatch, *, memory_value, ctx):
    """Parchea memoria + listener y devuelve (sesiones, escuchas, publicados)."""
    sessions: list[FakeSession] = []
    listened: list = []
    recalled: list[tuple] = []
    loaded: list = []

    async def fake_load(user_id):
        loaded.append(user_id)
        return memory_value

    async def fake_publish(user_id, message):
        recalled.append((user_id, message))

    async def fake_listen(session):
        listened.append(session)

    def fake_session_factory():
        sess = FakeSession()
        sessions.append(sess)
        return sess

    monkeypatch.setattr(voice_agent.memory_service, "load", fake_load)
    monkeypatch.setattr(voice_agent.memory_service, "publish_recalled", fake_publish)
    monkeypatch.setattr(voice_agent, "_listen_for_updates", fake_listen)
    return sessions, listened, recalled, loaded, fake_session_factory


# --- _resolve_user_id ---


def test_resolve_prefers_participant_over_claims():
    ctx = FakeCtx(
        room=FakeRoom({"p1": FakeParticipant("user-part")}),
        claims=FakeClaims("user-claims"),
    )
    assert _resolve_user_id(ctx) == "user-part"


def test_resolve_uses_claims_when_no_participants():
    ctx = FakeCtx(room=FakeRoom({}), claims=FakeClaims("user-claims"))
    assert _resolve_user_id(ctx) == "user-claims"


def test_resolve_uses_claims_dict():
    ctx = FakeCtx(room=FakeRoom({}), claims={"identity": "user-dict"})
    assert _resolve_user_id(ctx) == "user-dict"


def test_resolve_anonymous_when_no_identity():
    assert _resolve_user_id(FakeCtx()) == "anonymous"
    assert _resolve_user_id(FakeCtx(room=FakeRoom({}), claims=None)) == "anonymous"
    # Participante sin identidad y claims sin identidad -> anonymous.
    ctx = FakeCtx(
        room=FakeRoom({"p1": FakeParticipant(None)}),
        claims=FakeClaims(None),
    )
    assert _resolve_user_id(ctx) == "anonymous"


def test_resolve_tolerates_broken_ctx():
    class Broken:
        @property
        def room(self):
            raise RuntimeError("room roto")

        def token_claims(self):
            raise RuntimeError("claims rotos")

    assert _resolve_user_id(Broken()) == "anonymous"


# --- build_welcome_instructions ---


def test_welcome_without_memory_uses_base():
    assert build_welcome_instructions(None) == WELCOME_INSTRUCTIONS
    assert build_welcome_instructions("") == WELCOME_INSTRUCTIONS
    assert build_welcome_instructions("   ") == WELCOME_INSTRUCTIONS


def test_welcome_with_memory_mentions_previous_work():
    out = build_welcome_instructions("mercados de Madrid")
    assert "mercados de Madrid" in out
    assert WELCOME_INSTRUCTIONS in out


# --- voice_entrypoint ---


@pytest.mark.asyncio
async def test_entrypoint_participant_identity_loads_memory_and_greets(monkeypatch):
    ctx = FakeCtx(
        room=FakeRoom({"p1": FakeParticipant("user-1")}),
        claims=FakeClaims("other"),
    )
    sessions, listened, recalled, loaded, factory = _entrypoint_harness(
        monkeypatch, memory_value="investigaste paneles solares", ctx=ctx
    )
    await voice_entrypoint(ctx, session_factory=factory, agent_factory=FakeAgent)
    await asyncio.sleep(0.05)

    assert loaded == ["user-1"]  # memoria del participante, no del claim.
    assert recalled == [("user-1", "investigaste paneles solares")]
    assert tools.USER_ID.get() == "user-1"
    assert len(sessions) == 1
    assert sessions[0].started[0]["room"] is ctx.room
    assert isinstance(sessions[0].started[0]["agent"], FakeAgent)
    assert len(listened) == 1 and listened[0] is sessions[0]
    assert len(sessions[0].replies) == 1
    assert "investigaste paneles solares" in sessions[0].replies[0]
    assert WELCOME_INSTRUCTIONS in sessions[0].replies[0]


@pytest.mark.asyncio
async def test_entrypoint_claims_identity_when_no_participant(monkeypatch):
    ctx = FakeCtx(room=FakeRoom({}), claims=FakeClaims("user-claims"))
    sessions, listened, recalled, loaded, factory = _entrypoint_harness(
        monkeypatch, memory_value="resumen previo", ctx=ctx
    )
    await voice_entrypoint(ctx, session_factory=factory, agent_factory=FakeAgent)
    await asyncio.sleep(0.05)

    assert loaded == ["user-claims"]
    assert recalled == [("user-claims", "resumen previo")]
    assert tools.USER_ID.get() == "user-claims"
    assert "resumen previo" in sessions[0].replies[0]


@pytest.mark.asyncio
async def test_entrypoint_without_memory_uses_base_welcome(monkeypatch):
    ctx = FakeCtx(
        room=FakeRoom({"p1": FakeParticipant("user-2")}), claims=None
    )
    sessions, listened, recalled, loaded, factory = _entrypoint_harness(
        monkeypatch, memory_value=None, ctx=ctx
    )
    await voice_entrypoint(ctx, session_factory=factory, agent_factory=FakeAgent)
    await asyncio.sleep(0.05)

    assert loaded == ["user-2"]
    assert recalled == []
    assert sessions[0].replies == [WELCOME_INSTRUCTIONS]


@pytest.mark.asyncio
async def test_entrypoint_anonymous_skips_memory(monkeypatch):
    ctx = FakeCtx()
    sessions, listened, recalled, loaded, factory = _entrypoint_harness(
        monkeypatch, memory_value=None, ctx=ctx
    )
    await voice_entrypoint(ctx, session_factory=factory, agent_factory=FakeAgent)
    await asyncio.sleep(0.05)

    # anonymous -> load(None) -> sin memoria, sin evento, USER_ID None.
    assert loaded == [None]
    assert recalled == []
    assert tools.USER_ID.get() is None
    assert sessions[0].replies == [WELCOME_INSTRUCTIONS]
    assert len(listened) == 1


@pytest.mark.asyncio
async def test_entrypoint_starts_listener_task(monkeypatch):
    """El listener arranca como tarea asyncio (no solo llamada directa)."""
    ctx = FakeCtx(room=FakeRoom({"p1": FakeParticipant("user-9")}))
    created = []
    real_create_task = asyncio.create_task

    def spy_create_task(coro, **kwargs):
        created.append(coro)
        return real_create_task(coro, **kwargs)

    sessions_holder: list[FakeSession] = []

    def factory():
        sess = FakeSession()
        sessions_holder.append(sess)
        return sess

    async def fake_load(_user_id):
        return None

    listened = []

    async def fake_listen(session):
        listened.append(session)

    monkeypatch.setattr(voice_agent.memory_service, "load", fake_load)
    monkeypatch.setattr(voice_agent, "_listen_for_updates", fake_listen)
    monkeypatch.setattr(asyncio, "create_task", spy_create_task)
    await voice_entrypoint(ctx, session_factory=factory, agent_factory=FakeAgent)
    await asyncio.sleep(0.05)
    await asyncio.sleep(0.05)  # deja completar la tarea fire-and-forget.
    assert len(created) == 1
    assert listened == sessions_holder


# --- Propagación de USER_ID (issue #8) ---


@pytest.mark.asyncio
async def test_dispatch_includes_user_id_when_set(monkeypatch):
    from backend.orchestrator import tasks as orch_tasks

    calls: list[dict] = []

    def fake_send_task(name, args=None, task_id=None, **kwargs):
        calls.append({"name": name, "args": args, "task_id": task_id})

    monkeypatch.setattr(orch_tasks.celery_app, "send_task", fake_send_task)
    tools._dispatch_orchestrator("t-1", "Investiga X", "user-1")
    tools._dispatch_orchestrator("t-2", "Investiga Y", None)
    assert calls[0] == {
        "name": "run_pipeline",
        "args": ["t-1", "Investiga X", "user-1"],
        "task_id": "t-1",
    }
    assert calls[1] == {
        "name": "run_pipeline",
        "args": ["t-2", "Investiga Y"],
        "task_id": "t-2",
    }


@pytest.mark.asyncio
async def test_delegate_propagates_user_id_from_context(monkeypatch):
    from backend.decision.schemas import RouteAction, RouteDecision

    seen: list = []

    def fake_dispatch(task_id, goal, user_id=None):
        seen.append((task_id, goal, user_id))

    async def fake_route(_task_id, _goal):
        return RouteDecision(
            action=RouteAction.ORCHESTRATOR, reason="test", model="gpt-4o"
        )

    monkeypatch.setattr(tools, "_dispatch_orchestrator", fake_dispatch)
    monkeypatch.setattr("backend.decision.router.route", fake_route)

    class Ctx:
        session = object()

    tools.USER_ID.set("user-claims")
    try:
        await tools.delegate_complex_task_core(Ctx(), "Investiga el mercado")
    finally:
        tools.USER_ID.set(None)
    assert len(seen) == 1
    assert seen[0][1] == "Investiga el mercado"
    assert seen[0][2] == "user-claims"
