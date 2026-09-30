"""Tests de telefonía SIP/PSTN (entrada real y llamadas salientes).

Todo el acceso a LiveKit va con clientes fake inyectados: cero coste real.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api import main
from backend.config import settings
from backend.voice import sip, tools


@pytest.fixture
def sip_configured(monkeypatch):
    monkeypatch.setattr(settings, "sip_enabled", True)
    monkeypatch.setattr(settings, "sip_trunk_id", "tr_test123")
    monkeypatch.setattr(settings, "sip_number", "+34910000000")


@pytest.fixture
def sip_disabled(monkeypatch):
    monkeypatch.setattr(settings, "sip_enabled", False)
    monkeypatch.setattr(settings, "sip_trunk_id", "")


@pytest.fixture
def clean_state():
    sip.CALLERS.clear()
    tools.ACTIVE_TASKS.clear()
    yield
    sip.CALLERS.clear()
    tools.ACTIVE_TASKS.clear()


# --- Normalización E.164 ----------------------------------------------------


def test_normalize_phone_accepts_e164_variants():
    assert sip.normalize_phone("+34910000000") == "+34910000000"
    assert sip.normalize_phone(" +34 910-000-000 ") == "+34910000000"
    assert sip.normalize_phone("+34(910)000000") == "+34910000000"


def test_normalize_phone_rejects_invalid():
    for raw in ["", "910000000", "abc", "+34", "+0", "+34 91", "++34910000000"]:
        with pytest.raises(ValueError):
            sip.normalize_phone(raw)


# --- Flag de habilitación ----------------------------------------------------


def test_sip_enabled_requires_flag_and_trunk(sip_configured):
    assert sip.sip_enabled() is True


def test_sip_disabled_without_trunk(monkeypatch):
    monkeypatch.setattr(settings, "sip_enabled", True)
    monkeypatch.setattr(settings, "sip_trunk_id", "")
    assert sip.sip_enabled() is False


def test_sip_disabled_without_flag(monkeypatch):
    monkeypatch.setattr(settings, "sip_enabled", False)
    monkeypatch.setattr(settings, "sip_trunk_id", "tr_test123")
    assert sip.sip_enabled() is False


# --- Registro de llamantes ----------------------------------------------------


def test_register_peek_pop_caller(clean_state):
    assert sip.peek_caller("room-demo") is None
    sip.register_caller("room-demo", "+34910000000")
    assert sip.peek_caller("room-demo") == "+34910000000"
    assert sip.pop_caller("room-demo") == "+34910000000"
    assert sip.pop_caller("room-demo") is None


def test_register_caller_rejects_invalid_phone(clean_state):
    with pytest.raises(ValueError):
        sip.register_caller("room-demo", "no-es-un-numero")


def test_pending_callback_only_with_active_task(clean_state):
    sip.register_caller("room-demo", "+34910000000")
    # Sin tarea activa no hay rellamada aunque haya número.
    assert sip.pending_callback_for("room-demo") is None
    tools.ACTIVE_TASKS["room-demo"] = {"task_id": "t-1", "goal": "Investiga"}
    assert sip.pending_callback_for("room-demo") == "+34910000000"


def test_snapshot_diff_detects_tasks_created_during_session(clean_state):
    tools.ACTIVE_TASKS["other"] = {"task_id": "old-1", "goal": "Previa"}
    before = sip.snapshot_active_task_ids()
    tools.ACTIVE_TASKS["room-demo"] = {"task_id": "new-1", "goal": "Actual"}
    assert sip.session_pending_task_ids(before) == ["new-1"]
    assert sip.session_pending_task_ids(sip.snapshot_active_task_ids()) == []


# --- Detección del llamante SIP -------------------------------------------------


class _FakeParticipant:
    def __init__(self, identity="", attributes=None) -> None:
        self.identity = identity
        self.attributes = attributes or {}


class _FakeRoom:
    def __init__(self, participants) -> None:
        self.remote_participants = participants


def test_extract_caller_phone_from_sip_attributes():
    room = _FakeRoom(
        {"p1": _FakeParticipant("sip-user", {"sip.phoneNumber": "+34600000000"})}
    )
    assert sip.extract_caller_phone(room) == "+34600000000"


def test_extract_caller_phone_from_identity_e164():
    room = _FakeRoom([_FakeParticipant("+34600000001")])
    assert sip.extract_caller_phone(room) == "+34600000001"


def test_extract_caller_phone_none_for_webrtc():
    room = _FakeRoom({"p1": _FakeParticipant("user-ab12cd34")})
    assert sip.extract_caller_phone(room) is None
    assert sip.extract_caller_phone(_FakeRoom({})) is None
    assert sip.extract_caller_phone(_FakeRoom([])) is None


# --- Llamada saliente (mock del cliente LiveKit) ---------------------------------


class _FakeSipApi:
    def __init__(self, fail: Exception | None = None) -> None:
        self.requests: list = []
        self.fail = fail

    async def create_sip_participant(self, request):
        self.requests.append(request)
        if self.fail is not None:
            raise self.fail
        return type("Info", (), {"participant_id": "sip-part-1"})()


class _FakeClient:
    def __init__(self, fail: Exception | None = None) -> None:
        self.sip = _FakeSipApi(fail)
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_place_outbound_call_builds_request(sip_configured, clean_state):
    client = _FakeClient()
    result = await sip.place_outbound_call(
        "+34600000000", "demo", participant_identity="callback-abc", api_client=client
    )
    assert result["phone_number"] == "+34600000000"
    assert result["room"] == "demo"
    assert result["participant_identity"] == "callback-abc"
    assert result["participant_id"] == "sip-part-1"
    (request,) = client.sip.requests
    assert request.sip_call_to == "+34600000000"
    assert request.room_name == "demo"
    assert request.sip_trunk_id == "tr_test123"
    assert request.participant_identity == "callback-abc"


@pytest.mark.asyncio
async def test_place_outbound_call_generates_identity(sip_configured, clean_state):
    client = _FakeClient()
    result = await sip.place_outbound_call("+34600000000", "demo", api_client=client)
    assert result["participant_identity"].startswith("callback-")


@pytest.mark.asyncio
async def test_place_outbound_call_requires_config(sip_disabled, clean_state):
    with pytest.raises(sip.SIPConfigError):
        await sip.place_outbound_call(
            "+34600000000", "demo", api_client=_FakeClient()
        )


@pytest.mark.asyncio
async def test_place_outbound_call_validates_phone(sip_configured, clean_state):
    with pytest.raises(ValueError):
        await sip.place_outbound_call("no-valido", "demo", api_client=_FakeClient())


@pytest.mark.asyncio
async def test_place_outbound_call_requires_room(sip_configured, clean_state):
    with pytest.raises(ValueError):
        await sip.place_outbound_call("+34600000000", "  ", api_client=_FakeClient())


@pytest.mark.asyncio
async def test_place_outbound_call_wraps_provider_errors(sip_configured, clean_state):
    client = _FakeClient(fail=RuntimeError("trunk caído"))
    with pytest.raises(RuntimeError, match="No se pudo llamar"):
        await sip.place_outbound_call("+34600000000", "demo", api_client=client)


# --- Rellamada al colgar -----------------------------------------------------------


@pytest.mark.asyncio
async def test_callback_results_dials_when_configured(
    sip_configured, clean_state, monkeypatch
):
    from backend.voice import agent as voice_agent

    calls: list[tuple[str, str]] = []

    async def fake_place(phone: str, room_name: str, **kwargs):
        calls.append((phone, room_name))
        return {"phone_number": phone, "room": room_name}

    monkeypatch.setattr(sip, "place_outbound_call", fake_place)
    sip.register_caller("room-demo", "+34600000000")
    await voice_agent._callback_pending_results("demo", "room-demo")
    assert calls == [("+34600000000", "demo")]
    # El número se consume para no rellamar dos veces.
    assert sip.peek_caller("room-demo") is None


@pytest.mark.asyncio
async def test_callback_results_noop_without_caller(
    sip_configured, clean_state, monkeypatch
):
    from backend.voice import agent as voice_agent

    async def fake_place(*args, **kwargs):  # pragma: no cover
        raise AssertionError("no debería marcar sin llamante")

    monkeypatch.setattr(sip, "place_outbound_call", fake_place)
    await voice_agent._callback_pending_results("demo", "room-demo")


@pytest.mark.asyncio
async def test_callback_results_noop_when_sip_disabled(
    sip_disabled, clean_state, monkeypatch
):
    from backend.voice import agent as voice_agent

    async def fake_place(*args, **kwargs):  # pragma: no cover
        raise AssertionError("no debería marcar con SIP deshabilitado")

    monkeypatch.setattr(sip, "place_outbound_call", fake_place)
    sip.register_caller("room-demo", "+34600000000")
    await voice_agent._callback_pending_results("demo", "room-demo")


def test_room_key_prefixed_by_room_name():
    from backend.voice import agent as voice_agent

    class Ctx:
        room = type("Room", (), {"name": "demo"})()

    assert voice_agent._room_key(Ctx()) == "room-demo"


# --- Endpoints HTTP -----------------------------------------------------------------


def test_sip_status_reports_disabled(sip_disabled):
    client = TestClient(main.app)
    body = client.get("/sip/status").json()
    assert body["enabled"] is False


def test_sip_status_reports_enabled(sip_configured):
    client = TestClient(main.app)
    body = client.get("/sip/status").json()
    assert body == {"enabled": True, "number": "+34910000000"}


def test_sip_call_endpoint_dials(sip_configured, monkeypatch):
    calls: list[tuple[str, str]] = []

    async def fake_place(phone: str, room_name: str, **kwargs):
        calls.append((phone, room_name))
        return {"phone_number": phone, "room": room_name,
                "participant_identity": "callback-x", "participant_id": "p1"}

    monkeypatch.setattr("backend.voice.sip.place_outbound_call", fake_place)
    client = TestClient(main.app)
    resp = client.post("/sip/call", json={"phone_number": "+34600000000", "room": "demo"})
    assert resp.status_code == 200
    assert resp.json()["phone_number"] == "+34600000000"
    assert calls == [("+34600000000", "demo")]


def test_sip_call_rejects_invalid_phone(sip_configured):
    client = TestClient(main.app)
    resp = client.post("/sip/call", json={"phone_number": "xxx", "room": "demo"})
    assert resp.status_code == 422


def test_sip_call_requires_room(sip_configured):
    client = TestClient(main.app)
    resp = client.post("/sip/call", json={"phone_number": "+34600000000", "room": "  "})
    assert resp.status_code == 422


def test_sip_call_501_without_trunk(sip_disabled):
    client = TestClient(main.app)
    resp = client.post("/sip/call", json={"phone_number": "+34600000000", "room": "demo"})
    assert resp.status_code == 501


def test_sip_call_502_when_provider_fails(sip_configured, monkeypatch):
    async def fake_place(*args, **kwargs):
        raise RuntimeError("No se pudo llamar: trunk caído")

    monkeypatch.setattr("backend.voice.sip.place_outbound_call", fake_place)
    client = TestClient(main.app)
    resp = client.post("/sip/call", json={"phone_number": "+34600000000", "room": "demo"})
    assert resp.status_code == 502
