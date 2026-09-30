from fastapi.testclient import TestClient

from backend.api import main
from backend.config import Settings


def _dummy_settings() -> Settings:
    s = Settings()
    s.livekit_url = "wss://dev.livekit.cloud"
    s.livekit_api_key = "devkey"
    s.livekit_api_secret = "devsecret"
    return s


def test_token_endpoint(monkeypatch):
    monkeypatch.setattr(main, "settings", _dummy_settings())
    client = TestClient(main.app)
    resp = client.get("/token?room=prueba")
    assert resp.status_code == 200
    body = resp.json()
    assert body["wsUrl"] == "wss://dev.livekit.cloud"
    assert body["room"] == "prueba"
    assert body["identity"].startswith("participant-")
    assert body["token"].count(".") == 2


def test_token_returns_provided_identity(monkeypatch):
    monkeypatch.setattr(main, "settings", _dummy_settings())
    client = TestClient(main.app)
    resp = client.get("/token?room=prueba&identity=alice")
    assert resp.status_code == 200
    assert resp.json()["identity"] == "alice"


def test_token_requires_credentials(monkeypatch):
    s = _dummy_settings()
    s.livekit_api_key = ""
    s.livekit_api_secret = ""
    monkeypatch.setattr(main, "settings", s)
    client = TestClient(main.app)
    resp = client.get("/token?room=prueba")
    assert resp.status_code == 500


def test_index_serves_page():
    client = TestClient(main.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Respuesta" in resp.text
    assert "Iniciar tarea" in resp.text


def test_debug_run_dispatches_to_celery(monkeypatch):
    import backend.orchestrator.tasks as tasks

    calls = {}

    class Fake:
        @staticmethod
        def delay(**kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(tasks, "run_pipeline", Fake())
    client = TestClient(main.app)
    resp = client.post("/debug/run", json={"goal": "  probar redis  "})
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"].startswith("web-")
    assert calls["goal"] == "probar redis"
    assert calls["task_id"] == body["task_id"]


def test_debug_run_requires_goal():
    client = TestClient(main.app)
    resp = client.post("/debug/run", json={"goal": "   "})
    assert resp.status_code == 400