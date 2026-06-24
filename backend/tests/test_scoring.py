import pytest
from app.core.scoring import (
    compute_accuracy_score,
    compute_composite_score,
    compute_tool_precision,
    normalize_cost,
    normalize_latency,
)
from app.schemas.run import ScoreWeights


def test_normalize_latency_fast():
    assert normalize_latency(300) == 1.0


def test_normalize_latency_slow():
    assert normalize_latency(10000) == 0.0


def test_normalize_cost_cheap():
    assert normalize_cost(0.0005) == 1.0


def test_compute_composite_score_perfect():
    weights = ScoreWeights(
        accuracy_weight=0.2,
        hallucination_weight=0.2,
        tool_precision_weight=0.2,
        latency_weight=0.2,
        cost_weight=0.2,
    )
    score = compute_composite_score(1.0, 0.0, 1.0, 400, 0.0005, weights)
    assert score == 1.0


def test_compute_accuracy_identical():
    text = "The quick brown fox jumps over the lazy dog"
    score = compute_accuracy_score(text, text)
    assert score >= 0.9


def test_compute_tool_precision_f1():
    score = compute_tool_precision(["a", "b"], ["a", "b"])
    assert score == 1.0


def test_compute_tool_precision_partial():
    score = compute_tool_precision(["a", "b"], ["a", "c"])
    assert 0 < score < 1.0
