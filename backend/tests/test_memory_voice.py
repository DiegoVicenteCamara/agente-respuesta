"""Tests de la capa de voz con memoria: bienvenida y resolución de identidad."""

from types import SimpleNamespace

from backend.voice import agent


def test_build_welcome_without_memory_uses_base_instructions():
    welcome = agent.build_welcome_instructions(None)
    assert welcome == agent.WELCOME_INSTRUCTIONS
    assert "última vez" not in welcome


def test_build_welcome_mentions_previous_work():
    welcome = agent.build_welcome_instructions("investigaste el mercado inmobiliario")
    assert welcome.startswith(agent.WELCOME_INSTRUCTIONS)
    assert "investigaste el mercado inmobiliario" in welcome


class _FakeParticipant:
    def __init__(self, identity: str, is_agent: bool = False) -> None:
        self.identity = identity
        self.is_agent = is_agent


def _fake_ctx(participants=None, claims=None) -> SimpleNamespace:
    room = SimpleNamespace(remote_participants=participants or {})
    return SimpleNamespace(room=room, token_claims=lambda: claims or {})


def test_resolve_user_id_prefers_human_participant():
    ctx = _fake_ctx(
        {
            "p1": _FakeParticipant("alice"),
            "p2": _FakeParticipant("agente", is_agent=True),
        },
        claims={"identity": "alice"},
    )
    assert agent._resolve_user_id(ctx) == "alice"


def test_resolve_user_id_falls_back_to_token_claims():
    ctx = _fake_ctx(claims={"identity": "desde-token"})
    assert agent._resolve_user_id(ctx) == "desde-token"


def test_resolve_user_id_defaults_to_anonymous():
    ctx = _fake_ctx()
    assert agent._resolve_user_id(ctx) == "anonymous"