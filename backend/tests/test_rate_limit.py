"""Issue #48: rate-limit en /token y /debug/run (429 + Retry-After)."""

from fastapi.testclient import TestClient

from backend.api import main
from backend.config import Settings


def _dummy_settings(token_per_min: int = 30, debug_per_min: int = 10) -> Settings:
    s = Settings()
    s.livekit_url = "wss://dev.livekit.cloud"
    s.livekit_api_key = "devkey"
    s.livekit_api_secret = "devsecret"
    s.rate_limit_token_per_min = token_per_min
    s.rate_limit_debug_per_min = debug_per_min
    return s


def test_token_rate_limit_returns_429_with_retry_after(monkeypatch):
    main._reset_rate_limits()
    monkeypatch.setattr(main, "settings", _dummy_settings(token_per_min=3))
    client = TestClient(main.app)
    for _ in range(3):
        resp = client.get("/token?room=prueba")
        assert resp.status_code == 200
    limited = client.get("/token?room=prueba")
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    assert int(limited.headers["Retry-After"]) >= 1
    assert "Demasiadas peticiones" in limited.json()["detail"]


def test_debug_run_rate_limit_does_not_enqueue(monkeypatch):
    import backend.orchestrator.tasks as tasks

    main._reset_rate_limits()
    monkeypatch.setattr(main, "settings", _dummy_settings(debug_per_min=2))
    calls: list[dict] = []

    class Fake:
        @staticmethod
        def delay(**kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(tasks, "run_pipeline", Fake())
    client = TestClient(main.app)
    for _ in range(2):
        resp = client.post("/debug/run", json={"goal": "probar límite"})
        assert resp.status_code == 200
    assert len(calls) == 2
    limited = client.post("/debug/run", json={"goal": "probar límite"})
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    assert "Demasiadas peticiones" in limited.json()["detail"]
    # El trabajo excedente no se encola en Celery.
    assert len(calls) == 2


def test_traffic_under_limit_works_as_before(monkeypatch):
    import backend.orchestrator.tasks as tasks

    main._reset_rate_limits()
    monkeypatch.setattr(main, "settings", _dummy_settings())
    monkeypatch.setattr(tasks, "run_pipeline", type("Fake", (), {"delay": staticmethod(lambda **k: None)})())
    client = TestClient(main.app)
    assert client.get("/token?room=prueba").status_code == 200
    assert client.post("/debug/run", json={"goal": "hola"}).status_code == 200


def test_rate_limit_settings_defaults(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_TOKEN_PER_MIN", raising=False)
    monkeypatch.delenv("RATE_LIMIT_DEBUG_PER_MIN", raising=False)
    s = Settings()
    assert s.rate_limit_token_per_min == 30
    assert s.rate_limit_debug_per_min == 10
