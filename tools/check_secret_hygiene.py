"""Higiene de secretos para CI (issue #39).

Verifica sin dependencias externas:
1. ``.env`` está ignorado por git (``.gitignore`` + ``git check-ignore``).
2. ``.env.example`` no contiene valores con pinta real (``sk-``, PATs,
   claves privadas o secretos largos sin placeholder).

Uso en CI (job ``secret-scan``)::

    python tools/check_secret_hygiene.py

Sale con código 0 si todo está limpio, 1 con diagnóstico si hay
violaciones. El escaneo de patrones tipo gitleaks sobre el diff/PR lo
hace el paso ``gitleaks`` del workflow; este script es el check
complementario determinista (sin red, <30s).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]

# Patrones de secreto real (alineados con las reglas por defecto de gitleaks).
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),  # OpenAI y similares
    re.compile(r"sk-proj-[A-Za-z0-9_\-]{10,}"),  # OpenAI project keys
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),  # GitHub PAT clásico
    re.compile(r"github_pat_[A-Za-z0-9_]{22,}"),  # GitHub fine-grained PAT
    re.compile(r"gho_[A-Za-z0-9]{36,}"),  # GitHub OAuth
    re.compile(r"xox[bap]-?[A-Za-z0-9\-]{10,}"),  # Slack
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]

# Subcadenas que marcan un valor como placeholder (no real).
PLACEHOLDER_MARKERS = (
    "TU_",
    "YOUR_",
    "EXAMPLE",
    "PLACEHOLDER",
    "CHANGEME",
    "REPLACE",
    "TODO",
    "XXX",
    "SAMPL",
)


def _is_placeholder(value: str) -> bool:
    """True si el valor es vacío o un placeholder evidente."""
    v = value.strip().strip("\"'")
    if not v:
        return True
    upper = v.upper()
    if any(m in upper for m in PLACEHOLDER_MARKERS):
        return True
    if v.startswith("<") and v.endswith(">"):
        return True
    # URLs/identificadores no secretos con dominio de ejemplo.
    if upper in {"TRUE", "FALSE"}:
        return True
    return False


def contains_secret(text: str) -> bool:
    """True si el texto contiene un patrón de secreto real."""
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            return True
    return False


def check_gitignore(repo: pathlib.Path = REPO) -> list[str]:
    """Verifica que ``.env`` está ignorado por git."""
    errors: list[str] = []
    gitignore = repo / ".gitignore"
    if not gitignore.is_file():
        return [".gitignore no existe"]
    content = gitignore.read_text(encoding="utf-8")
    # Línea .env (exacta o con prefijos como /.env, *.env no vale).
    lines = [
        ln.strip()
        for ln in content.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not any(ln in {".env", "/.env"} for ln in lines):
        errors.append(".gitignore no ignora .env (falta línea '.env')")
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", ".env"],
            cwd=repo,
            capture_output=True,
        )
        if proc.returncode != 0:
            errors.append("git check-ignore .env no ignora (.env sería commiteable)")
    except FileNotFoundError:
        errors.append("git no disponible para verificar check-ignore")
    return errors


def check_env_example(repo: pathlib.Path = REPO) -> list[str]:
    """Verifica que ``.env.example`` no contiene valores reales."""
    errors: list[str] = []
    path = repo / ".env.example"
    if not path.is_file():
        return [".env.example no existe"]
    for lineno, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'").strip()
        if not value or _is_placeholder(value):
            continue
        # 1. Patrón de secreto conocido en el valor.
        if contains_secret(value):
            errors.append(
                f".env.example:{lineno} {key} parece un secreto real ({value[:12]}…)"
            )
            continue
        # 2. Claves/secretos largos sin marcador de placeholder.
        if re.search(r"SECRET|API_KEY|TOKEN|PASSWORD|PRIVATE", key, re.I):
            # Valores cortos no secretos (puertos, modelos, flags) se permiten;
            # solo fallan los que parecen material real (>16 chars) o URLs con
            # credenciales embebidas.
            if len(value) > 16 or contains_secret(f"{key}={value}"):
                errors.append(
                    f".env.example:{lineno} {key} con valor largo sin placeholder"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chequeo de higiene de secretos")
    parser.add_argument(
        "--repo", default=str(REPO), help="Raíz del repositorio a verificar"
    )
    args = parser.parse_args(argv)
    repo = pathlib.Path(args.repo)

    errors = check_gitignore(repo) + check_env_example(repo)
    if errors:
        for err in errors:
            print(f"secret-hygiene FAIL: {err}")
        return 1
    print("secret-hygiene OK: .env ignorado y .env.example sin valores reales")
    return 0


if __name__ == "__main__":
    sys.exit(main())
