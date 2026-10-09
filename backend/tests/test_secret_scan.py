"""Higiene de secretos en CI (issue #39).

Verifica que el job ``secret-scan`` existe y que la higiene de ``.env``
se cumple: ``.env`` ignorado, ``.env.example`` sin valores reales y
README documentando el check obligatorio.

Los secretos de prueba se construyen en runtime (``"sk-" + "a"*25``)
para no commitear ningún patrón literal que haría fallar a gitleaks
sobre ``main``.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = REPO / ".github" / "workflows" / "secret-scan.yml"
SCRIPT = REPO / "tools" / "check_secret_hygiene.py"

sys.path.insert(0, str(REPO / "tools"))
import check_secret_hygiene as hygiene  # noqa: E402


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workflow_secret_scan_existe():
    assert WORKFLOW.is_file(), "falta .github/workflows/secret-scan.yml"
    yml = _read(WORKFLOW)
    assert "gitleaks" in yml.lower(), "el workflow debe invocar gitleaks"
    assert "check_secret_hygiene" in yml, "el workflow debe correr el check de higiene"
    assert "pull_request" in yml, "debe correr en pull_request"
    assert "push" in yml, "debe correr en push a main"
    assert "contents: read" in yml, "permisos mínimos esperados"


def test_workflow_timeout_acotado():
    yml = _read(WORKFLOW)
    # El issue exige verde en <3 min: el timeout debe ser <=3.
    import re

    m = re.search(r"timeout-minutes:\s*(\d+)", yml)
    assert m, "el job debe declarar timeout-minutes"
    assert int(m.group(1)) <= 3


def test_script_higiene_existe_y_es_ejecutable():
    assert SCRIPT.is_file()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


def test_env_ignorado_por_git():
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert any(
        ln.strip() in {".env", "/.env"}
        for ln in gitignore.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    )
    proc = subprocess.run(
        ["git", "check-ignore", "-q", ".env"], cwd=REPO, capture_output=True
    )
    assert proc.returncode == 0, ".env debería estar ignorado (git check-ignore)"
    assert hygiene.check_gitignore(REPO) == []


def test_env_example_sin_valores_reales():
    content = _read(REPO / ".env.example")
    # Ningún patrón literal de secreto en el fichero commiteado.
    assert "sk-" not in content, ".env.example no debe contener prefijo sk-"
    assert hygiene.check_env_example(REPO) == []
    assert not hygiene.contains_secret(content)


def test_fake_secret_hace_fallar_el_check():
    # Secreto de prueba del issue, ensamblado en runtime para no dejar
    # un patrón literal en el repo (gitleaks lo vería en main).
    fake_openai = "sk-" + "a" * 25
    assert hygiene.contains_secret(f"OPENAI_API_KEY={fake_openai}")
    fake_ghp = "ghp_" + "b" * 36
    assert hygiene.contains_secret(fake_ghp)
    fake_aws = "AKIA" + "C" * 16
    assert hygiene.contains_secret(fake_aws)
    hdr = "-" * 5 + "BEGIN PRIVATE KEY" + "-" * 5
    assert hygiene.contains_secret(hdr)


def test_env_example_con_secreto_falla(tmp_path):
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    fake = "sk-" + "f" * 30
    (tmp_path / ".env.example").write_text(
        f"OPENAI_API_KEY={fake}\n", encoding="utf-8"
    )
    errors = hygiene.check_env_example(tmp_path)
    assert errors, "un .env.example con secreto debe fallar"


def test_readme_documenta_secret_scan_obligatorio():
    readme = _read(REPO / "README.md")
    assert "secret-scan" in readme
    low = readme.lower()
    assert "obligatorio" in low
    # Debe mencionarse junto al check de tests.
    assert "test" in low
