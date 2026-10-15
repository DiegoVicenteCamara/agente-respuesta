"""Tests del panel accesible (issue #40): live regions, banner de error y reintento."""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
PANEL = REPO / "web" / "index.html"


def _html() -> str:
    return PANEL.read_text(encoding="utf-8")


def test_panel_exists():
    assert PANEL.is_file()


def test_status_has_live_region():
    html = _html()
    m = re.search(r'<p[^>]*id="status"[^>]*>', html)
    assert m, "#status no encontrado"
    assert 'aria-live="polite"' in m.group(0)


def test_log_has_log_role_and_live():
    html = _html()
    m = re.search(r'<ul[^>]*id="log"[^>]*>', html)
    assert m, "#log no encontrado"
    tag = m.group(0)
    assert 'role="log"' in tag
    assert 'aria-live="polite"' in tag


def test_agents_has_log_role_and_live():
    html = _html()
    m = re.search(r'<div[^>]*id="agents"[^>]*>', html)
    assert m, "#agents no encontrado"
    tag = m.group(0)
    assert 'role="log"' in tag
    assert 'aria-live="polite"' in tag


def test_buttons_have_aria_labels():
    html = _html()
    for btn_id in ("connect", "hangup", "mute", "runTask"):
        m = re.search(r'<button[^>]*id="%s"[^>]*>' % btn_id, html)
        assert m, f"botón #{btn_id} no encontrado"
        assert "aria-label" in m.group(0), f"botón #{btn_id} sin aria-label"


def test_banner_exists_with_alert_and_retry():
    html = _html()
    m = re.search(r'<div[^>]*id="banner"[^>]*>', html)
    assert m, "#banner no encontrado"
    tag = m.group(0)
    assert 'role="alert"' in tag
    assert "assertive" in tag
    assert 'tabindex="-1"' in tag
    assert "hidden" in tag
    assert 'id="bannerText"' in html
    assert 'id="bannerRetry"' in html
    assert "Reintentar" in html


def test_banner_css_hides_when_hidden():
    html = _html()
    assert "#banner[hidden]" in html


def test_js_distinguishes_empty_vs_error_and_retries():
    html = _html()
    # helpers con foco gestionado
    assert "function showBanner" in html
    assert "function hideBanner" in html
    assert "bannerEl.focus" in html
    # mensajes diferenciados: vacío sigue siendo "Aún no hay tareas"
    assert "Aún no hay tareas en el historial." in html
    # error usa banner, no el mensaje de vacío
    assert "Redis no disponible" in html
    # loadHistory: !res.ok y catch muestran banner
    assert html.count('showBanner("Redis no disponible') >= 2
    # reintento manual recarga historial
    assert 'bannerRetry' in html and "loadHistory()" in html
    # SSE cortado: banner + rehabilita Iniciar tarea
    assert "Bus no disponible" in html
    assert "runBtn.disabled = false" in html


def test_index_served_contains_banner_and_live_regions():
    from fastapi.testclient import TestClient

    from backend.api import main

    client = TestClient(main.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'id="banner"' in resp.text
    assert 'aria-live="polite"' in resp.text
    assert 'role="log"' in resp.text
