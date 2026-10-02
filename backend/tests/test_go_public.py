"""Tests go-public (issue: hacer el repositorio público).

Fija la auditoría de publicación: gobernanza presente, .gitignore que cubre
secretos, workflows sin volcado de claves y sin patrones de secretos en el
contenido trackeado.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
WORKFLOWS = REPO / ".github" / "workflows"
TEMPLATES = REPO / ".github" / "ISSUE_TEMPLATE"
ADR = (
    REPO
    / "docs"
    / "decisions"
    / "ADR-007-hacer-el-repositorio-publico-go-public-licencia-secretos-gobernanza.md"
)

SECRET_PATTERNS = (
    r"sk-[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{10,}",
    r"github_pat_[A-Za-z0-9_]{10,}",
    r"-----BEGIN (RSA )?PRIVATE KEY-----",
    r"xox[bap]-[A-Za-z0-9-]{10,}",
)
SKIP_DIRS = {".git", "graphify-out", "__pycache__", ".pytest_cache", ".venv",
             "node_modules", ".opencode"}


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ficheros_gobernanza_presentes():
    for name in ("LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"):
        assert (REPO / name).is_file(), name
    lic = _read(REPO / "LICENSE")
    assert "MIT License" in lic and "Diego Vicente" in lic
    contrib = _read(REPO / "CONTRIBUTING.md")
    assert "agent-ready" in contrib and ".env" in contrib
    sec = _read(REPO / "SECURITY.md")
    assert "SECRET" in sec.upper() or "secreto" in sec.lower()
    coc = _read(REPO / "CODE_OF_CONDUCT.md")
    assert "Contributor Covenant" in coc


def test_plantillas_y_funding_presentes():
    for name in ("config.yml", "feature.yml", "bug.yml", "security.yml",
                 "docs-ux-workflow.yml"):
        assert (TEMPLATES / name).is_file(), name
    feature = _read(TEMPLATES / "feature.yml")
    assert "agent-ready" in feature and "Criterios" in feature
    assert (REPO / ".github" / "PULL_REQUEST_TEMPLATE.md").is_file()
    pr = _read(REPO / ".github" / "PULL_REQUEST_TEMPLATE.md")
    assert "Closes #" in pr
    assert (REPO / ".github" / "FUNDING.yml").is_file()


def test_readme_con_badges_ci_y_licencia():
    readme = _read(REPO / "README.md")
    assert "workflows/test.yml/badge.svg" in readme
    assert "workflows/pages.yml/badge.svg" in readme
    assert "license-MIT" in readme or "(LICENSE)" in readme


def test_gitignore_cubre_secretos():
    gi = _read(REPO / ".gitignore")
    for entry in (".env", "logs/", "*.pem", "*.key"):
        assert entry in gi, entry
    assert "!.env.example" in gi
    assert (REPO / ".env.example").is_file()


def test_workflows_sin_volcado_de_secretos():
    for yml in WORKFLOWS.glob("*.yml"):
        content = _read(yml)
        low = content.lower()
        assert "echo ${{ secrets." not in low, yml.name
        assert "print(" not in low or "secrets." not in low, yml.name
        assert "secrets.OPENCODE_API_KEY" in content or "secrets.GITHUB_TOKEN" in content \
            or yml.name in ("test.yml", "pages.yml"), yml.name


def test_sin_patrones_de_secretos_en_contenido():
    offenders: list[str] = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix in (".png", ".jpg", ".ico", ".woff2"):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in SECRET_PATTERNS:
            if re.search(pat, text):
                offenders.append(f"{path.relative_to(REPO)}:{pat}")
    assert offenders == [], offenders


def test_adr_go_public_presente():
    assert ADR.is_file()
    content = _read(ADR)
    assert "## Status" in content and "## Decision" in content
    assert "MIT" in content and "topics" in content.lower()
