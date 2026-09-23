"""Tests del cliente Jev: normalización, fallback HTTP y timeouts."""

import pytest

from backend.decision import jev
from backend.decision.schemas import (
    ComplexityTier,
    DecisionNormalizationError,
    TargetWorker,
    TriageAnswer,
)

VALID_ANSWERS = {
    "target_worker": {"choice": "dialogue", "confidence": 0.9},
    "complexity_tier": {"choice": "low", "confidence": 0.85},
    "risk_index": {"score": 0.3, "confidence": 0.88},
    "is_prompt_injection": {"noul": 0.05},
}


def test_normalize_builds_strict_triage():
    triage = jev._normalize(dict(VALID_ANSWERS))
    assert isinstance(triage, TriageAnswer)
    assert triage.target_worker == TargetWorker.DIALOGUE
    assert triage.complexity_tier == ComplexityTier.LOW
    assert triage.risk_index == 0.3
    assert triage.is_prompt_injection == 0.05
    assert triage.confidence == 0.85  # mínimo de las confidencias presentes


def test_normalize_missing_key_raises():
    broken = {k: v for k, v in VALID_ANSWERS.items() if k != "risk_index"}
    with pytest.raises(DecisionNormalizationError):
        jev._normalize(broken)


def test_normalize_invalid_choice_raises():
    broken = dict(VALID_ANSWERS)
    broken["complexity_tier"] = {"choice": "ultra", "confidence": 0.8}
    with pytest.raises(DecisionNormalizationError):
        jev._normalize(broken)


async def test_classify_without_key_returns_none(monkeypatch):
    monkeypatch.setattr(jev.settings, "typesafe_api_key", "")
    assert await jev.classify("Hola") is None


async def test_classify_uses_http_fallback_when_lc_fails(monkeypatch):
    monkeypatch.setattr(jev.settings, "typesafe_api_key", "sk-test")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("langchain typesafe no disponible")

    async def http_ok(*_args, **_kwargs):
        return dict(VALID_ANSWERS)

    monkeypatch.setattr(jev, "_lc_classify", boom)
    monkeypatch.setattr(jev, "_http_classify", http_ok)
    triage = await jev.classify("Pregunta sencilla")
    assert triage is not None
    assert triage.target_worker == TargetWorker.DIALOGUE


async def test_classify_returns_none_when_all_transports_fail(monkeypatch):
    monkeypatch.setattr(jev.settings, "typesafe_api_key", "sk-test")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("fallo total")

    monkeypatch.setattr(jev, "_lc_classify", boom)
    monkeypatch.setattr(jev, "_http_classify", boom)
    assert await jev.classify("X") is None


async def test_classify_timeout_is_enforced(monkeypatch):
    import asyncio
    import time

    monkeypatch.setattr(jev.settings, "typesafe_api_key", "sk-test")
    monkeypatch.setattr(jev.settings, "routing_timeout_ms", 50)

    async def slow(*_args, **_kwargs):
        await asyncio.sleep(1.0)

    monkeypatch.setattr(jev, "_lc_classify", slow)
    monkeypatch.setattr(jev, "_http_classify", slow)

    started = time.perf_counter()
    result = await jev.classify("X")
    elapsed = time.perf_counter() - started
    assert result is None
    assert elapsed < 0.5