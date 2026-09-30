"""Tests de la landing estática de GitHub Pages (issue landing + ADR-004)."""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
INDEX = DOCS / "index.html"
CSS = DOCS / "styles.css"
PAGES_YML = REPO / ".github" / "workflows" / "pages.yml"
README = REPO / "README.md"
SITE_URL = "https://diegovicentecamara.github.io/agente-respuesta/"
REPO_URL = "https://github.com/DiegoVicenteCamara/agente-respuesta"


def _read(path: pathlib.Path) -> str:
    """Lee un fichero de texto UTF-8."""
    return path.read_text(encoding="utf-8")


def test_ficheros_publicacion_existen():
    """La fuente del sitio y el workflow de Pages existen."""
    assert INDEX.is_file()
    assert CSS.is_file()
    assert (DOCS / ".nojekyll").is_file()
    assert PAGES_YML.is_file()
    assert (DOCS / "decisions" / "ADR-004-landing-page-en-github-pages-desde-docs-con-deploy-por-actions.md").is_file()


def test_secciones_diataxis_presentes():
    """Pitch, arquitectura+diagrama, quickstart+modo prueba y enlaces a docs."""
    html = _read(INDEX)
    assert "subagentes proactivos" in html or "subagentes en" in html
    assert "arquitectura" in html.lower()
    assert "delegate_complex_task" in html
    assert "Redis" in html
    assert "LangGraph" in html
    assert "quickstart" in html.lower()
    assert "cp .env.example .env" in html
    assert "pip install -r backend/requirements.txt" in html
    assert "celery" in html and "uvicorn" in html
    assert "localhost:7860" in html
    assert "Modo prueba" in html and "Iniciar tarea" in html
    assert "/debug/run" in html and "/debug/stream" in html
    assert "agent-ready" in html
    assert "SPEC-jev-router" in html
    for adr in ("ADR-001", "ADR-002", "ADR-003", "ADR-004"):
        assert adr in html


def test_sin_framework_ni_demo_en_vivo():
    """HTML/CSS sin framework ni JS de demo; se declara sin demo en vivo."""
    html = _read(INDEX)
    low = html.lower()
    for fw in ("bootstrap", "tailwind", "react", "angular"):
        assert re.search(r"\b" + re.escape(fw) + r"\b", low) is None
    for lib in ("vue.js", "vue@", "next.js", "react.js"):
        assert lib not in low
    assert "<script" not in low
    assert "Sin demo en vivo" in html


def test_sin_secretos_en_lo_publicado():
    """El contenido publicado no incluye secretos ni claves."""
    html = _read(INDEX)
    css = _read(CSS)
    for content in (html, css):
        assert "sk-" not in content
        assert "ghp_" not in content
        assert "github_pat" not in content
        assert "BEGIN PRIVATE KEY" not in content
        assert "TU_API_KEY" not in content
    assert "LIVEKIT_API_SECRET=" not in html


def test_sin_backend_ni_web_en_publicacion():
    """docs/ no contiene backend/ ni web/ y el workflow solo publica docs/."""
    assert not (DOCS / "backend").exists()
    assert not (DOCS / "web").exists()
    yml = _read(PAGES_YML)
    assert "upload-pages-artifact" in yml
    assert "deploy-pages" in yml
    assert re.search(r"path:\s*docs\b", yml)
    assert "path: backend" not in yml and "path: web" not in yml


def test_enlaces_relativos_resuelven_a_fichero():
    """Todo href relativo de la landing existe en docs/ (ninguno roto)."""
    html = _read(INDEX)
    hrefs = re.findall(r'href="([^"]+)"', html)
    relativos = [h for h in hrefs if not h.startswith(("http", "#", "mailto:"))]
    assert relativos
    for href in relativos:
        target = (DOCS / href.split("#")[0]).resolve()
        assert str(target).startswith(str(DOCS.resolve())), href
        assert target.is_file(), href


def test_enlaces_cruzados_readme_landing():
    """README enlaza al sitio y la landing vuelve al README/repo."""
    readme = _read(README)
    html = _read(INDEX)
    assert SITE_URL in readme
    assert REPO_URL in html
    assert "Volver al README" in html or "README" in html
