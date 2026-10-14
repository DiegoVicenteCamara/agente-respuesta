"""Issue #50: docs/env.md cubre el 100% de claves de backend/config.py.

Verifica que la referencia operativa (.env) es completa y sin secretos:
- toda clave leída en backend/config.py está en docs/env.md y en .env.example
- los defaults documentados coinciden con el código
- README enlaza docs/env.md desde Configuración
- no hay secretos en docs/env.md ni en .env.example
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
CONFIG = REPO / "backend" / "config.py"
ENV_MD = REPO / "docs" / "env.md"
ENV_EXAMPLE = REPO / ".env.example"
README = REPO / "README.md"


def _config_keys() -> dict[str, str]:
    src = CONFIG.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for m in re.finditer(r'_get\(\s*"([A-Z0-9_]+)"(?:\s*,\s*"([^"]*)")?\s*\)', src):
        key, default = m.group(1), m.group(2)
        if default is None:
            default = ""
        # _load_pricing genera claves dinámicas PRICING_<SLUG>_PER_1M_{IN,OUT};
        # aparecen como f-string, así que se expanden aparte (ver abajo).
        if key.startswith("PRICING_"):
            continue
        found.setdefault(key, default)
    # Claves dinámicas de precios (defaults en _load_pricing).
    found.setdefault("PRICING_GPT_4O_MINI_PER_1M_IN", "0.15")
    found.setdefault("PRICING_GPT_4O_MINI_PER_1M_OUT", "0.60")
    found.setdefault("PRICING_GPT_4O_PER_1M_IN", "2.50")
    found.setdefault("PRICING_GPT_4O_PER_1M_OUT", "10.00")
    return found


def _env_example_keys() -> set[str]:
    keys: set[str] = set()
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Z0-9_]+)=", line)
        if m:
            keys.add(m.group(1))
    return keys


def test_env_md_existe_y_cubre_todas_las_claves():
    assert ENV_MD.is_file()
    md = ENV_MD.read_text(encoding="utf-8")
    expected = _config_keys()
    # La issue exige el 100% de claves de config.py (34 a día de hoy).
    assert len(expected) == 34, sorted(expected)
    for key in expected:
        assert f"`{key}`" in md, key


def test_defaults_documentados_coinciden_con_config():
    md = ENV_MD.read_text(encoding="utf-8")
    for key, default in _config_keys().items():
        shown = default if default else "(vacío)"
        # Cada fila de la tabla muestra el default exacto del código.
        assert f"`{key}`" in md
        assert shown in md, f"{key} default {default!r} no documentado"


def test_env_example_contiene_todas_las_claves():
    example = _env_example_keys()
    for key in _config_keys():
        assert key in example, key


def test_readme_enlaza_referencia_env():
    readme = README.read_text(encoding="utf-8")
    assert "docs/env.md" in readme


def test_sin_secretos_en_docs_y_example():
    import re as _re
    for path in (ENV_MD, ENV_EXAMPLE):
        content = path.read_text(encoding="utf-8")
        assert "BEGIN PRIVATE KEY" not in content
        assert "github_pat" not in content
        # Permite el placeholder sk-TU_API_KEY, prohíbe valores reales.
        for m in _re.finditer(r"sk-[A-Za-z0-9_-]+", content):
            assert "TU_API_KEY" in m.group(0), m.group(0)
        assert not _re.search(r"ghp_[A-Za-z0-9]{8,}", content)
    # .env.example solo placeholders, ningún secreto real con valor.
    assert "TU_API_KEY" in ENV_EXAMPLE.read_text(encoding="utf-8") or \
        "TU_SUBDOMINIO" in ENV_EXAMPLE.read_text(encoding="utf-8")


def test_modelo_precios_documentado():
    md = ENV_MD.read_text(encoding="utf-8")
    assert "cost_ready" in md
    assert "PRICING_" in md
    assert "COST_EUR_PER_USD" in md
    assert "estimate_cost_eur" in md
