from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.schemas import (
    AISystem,
    CallMetadata,
    Digest,
    RunMetadata,
    RunReport,
    ScoredPair,
    Signal,
)


def _make_system() -> AISystem:
    return AISystem(
        id="test-system",
        name="Test System",
        purpose="Test purpose",
        model_type="classifier",
        data_inputs=["data_a"],
        users=["analyst"],
        deployment_context="internal",
        known_risks=["bias"],
    )


def _make_signal() -> Signal:
    return Signal(
        id="test-signal",
        title="Test Signal",
        description="A test signal description.",
        date="2024-01-01",
        source="Test Source",
        source_url="https://example.com",
        tags=["bias"],
    )


def _make_run_metadata() -> RunMetadata:
    return RunMetadata(
        run_timestamp=datetime.now(tz=timezone.utc),
        model_name="claude-haiku",
        retrieval_threshold=0.3,
        num_signals=10,
        num_systems=3,
        num_pairs_after_retrieval=20,
        num_pairs_scored=18,
        num_pairs_failed=2,
        elapsed_seconds=45.0,
    )


def test_ai_system_roundtrip():
    system = _make_system()
    assert AISystem.model_validate(system.model_dump()) == system


def test_signal_roundtrip():
    signal = _make_signal()
    assert Signal.model_validate(signal.model_dump()) == signal


def test_scored_pair_score_bounds():
    with pytest.raises(Exception):
        ScoredPair(
            signal_id="s", system_id="sys", cosine_similarity=0.5,
            relevance_score=5, justification="x", suggested_action="y", reasoning="z",
        )


def test_run_metadata_defaults():
    meta = _make_run_metadata()
    assert meta.total_tokens_in == 0
    assert meta.total_tokens_out == 0
    assert meta.total_estimated_cost_usd == 0.0
    assert meta.avg_latency_ms == 0.0


def test_call_metadata_roundtrip():
    call = CallMetadata(
        signal_id="sig-1",
        system_id="sys-1",
        model_id="claude-haiku",
        tokens_in=500,
        tokens_out=200,
        latency_ms=1234.5,
        estimated_cost_usd=0.001234,
        timestamp="2024-01-01T00:00:00+00:00",
    )
    assert CallMetadata.model_validate(call.model_dump()) == call


def test_run_report_roundtrip():
    report = RunReport(
        metadata=_make_run_metadata(),
        call_metadata=[],
    )
    assert RunReport.model_validate(report.model_dump()) == report


def test_digest_roundtrip():
    scored = ScoredPair(
        signal_id="sig-1",
        system_id="sys-1",
        cosine_similarity=0.45,
        relevance_score=3,
        justification="Relevant because...",
        suggested_action="Review X.",
        reasoning="Step by step...",
    )
    digest = Digest(
        metadata=_make_run_metadata(),
        systems=[_make_system()],
        signals=[_make_signal()],
        scored_pairs=[scored],
    )
    assert Digest.model_validate(digest.model_dump()) == digest
