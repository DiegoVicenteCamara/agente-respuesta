"""Tests de la política pura de ruteo (sin I/O)."""

import pytest

from backend.decision.schemas import (
    ComplexityTier,
    RouteAction,
    RoutingConfig,
    TargetWorker,
    TriageAnswer,
)
from backend.decision.router import decide

FAST_MODEL = "gpt-4o-mini"
ADVANCED_MODEL = "gpt-4o"
CFG = RoutingConfig()


def _triage(
    worker: str = "dialogue",
    tier: str = "low",
    risk: float = 0.1,
    injection: float = 0.0,
    confidence: float = 0.9,
) -> TriageAnswer:
    return TriageAnswer(
        target_worker=TargetWorker(worker),
        complexity_tier=ComplexityTier(tier),
        risk_index=risk,
        is_prompt_injection=injection,
        confidence=confidence,
    )


def test_fast_path_trivial_dialogue():
    decision = decide(_triage(), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.FAST
    assert decision.model == FAST_MODEL
    assert decision.reason == "trivial_fast_path"


def test_high_risk_triggers_propose_commit():
    decision = decide(_triage(risk=1.8), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.PROPOSE_COMMIT
    assert decision.reason == "critical_risk"


def test_reversible_risk_with_high_tier_triggers_propose_commit():
    decision = decide(_triage(tier="high", risk=1.2), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.PROPOSE_COMMIT


def test_reversible_risk_with_low_tier_escalates_to_orchestrator():
    decision = decide(_triage(tier="low", risk=1.2), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.ORCHESTRATOR
    assert decision.model == FAST_MODEL


def test_injection_blocks_regardless_of_worker_and_risk():
    decision = decide(
        _triage(worker="dialogue", tier="low", risk=0.1, injection=0.95),
        CFG,
        FAST_MODEL,
        ADVANCED_MODEL,
    )
    assert decision.action == RouteAction.BLOCK
    assert decision.reason == "injection_detected"


def test_research_worker_goes_to_orchestrator():
    decision = decide(_triage(worker="research"), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.ORCHESTRATOR
    assert decision.reason == "complex_task"


def test_dialogue_high_tier_uses_advanced_model():
    decision = decide(_triage(tier="high"), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.ORCHESTRATOR
    assert decision.model == ADVANCED_MODEL


def test_risk_above_fast_threshold_goes_to_orchestrator():
    decision = decide(_triage(worker="dialogue", tier="low", risk=0.8), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.ORCHESTRATOR
    assert decision.reason == "complex_task"


def test_unimplemented_domain_worker_escalates_to_orchestrator():
    decision = decide(_triage(worker="billing", tier="low", risk=0.1), CFG, FAST_MODEL, ADVANCED_MODEL)
    assert decision.action == RouteAction.ORCHESTRATOR


@pytest.mark.parametrize(
    ("confidence", "expected", "expected_model"),
    [
        (0.4, RouteAction.ORCHESTRATOR, FAST_MODEL),
        (0.6, RouteAction.FAST, FAST_MODEL),
    ],
)
def test_low_confidence_escalates_conservatively(confidence, expected, expected_model):
    decision = decide(
        _triage(worker="dialogue", tier="low", risk=0.1, confidence=confidence),
        CFG,
        FAST_MODEL,
        ADVANCED_MODEL,
    )
    assert decision.action == expected
    if expected == RouteAction.ORCHESTRATOR:
        assert decision.reason == "low_confidence"
    assert decision.model == expected_model


def test_low_confidence_never_degrades_injection_or_critical_risk():
    block = decide(
        _triage(risk=0.1, injection=0.9, confidence=0.2),
        CFG,
        FAST_MODEL,
        ADVANCED_MODEL,
    )
    assert block.action == RouteAction.BLOCK
    commit = decide(
        _triage(risk=1.9, injection=0.0, confidence=0.2),
        CFG,
        FAST_MODEL,
        ADVANCED_MODEL,
    )
    assert commit.action == RouteAction.PROPOSE_COMMIT


def test_triage_answer_enforces_strict_ranges():
    with pytest.raises(ValueError):
        TriageAnswer(
            target_worker=TargetWorker.DIALOGUE,
            complexity_tier=ComplexityTier.LOW,
            risk_index=3.0,
            is_prompt_injection=0.0,
            confidence=0.9,
        )
    with pytest.raises(ValueError):
        TriageAnswer(
            target_worker=TargetWorker.DIALOGUE,
            complexity_tier=ComplexityTier.LOW,
            risk_index=0.5,
            is_prompt_injection=1.5,
            confidence=0.9,
        )