"""Tests for SignalResult and CompositeScore frozen dataclasses."""

from src.models.signal import CompositeScore, SignalDirection, SignalResult


def test_signal_result_weighted_value():
    result = SignalResult(name="OBI", value=0.5, confidence=0.8, weight=0.3)
    assert abs(result.weighted_value - 0.12) < 0.001


def test_signal_result_zero_confidence():
    result = SignalResult(name="RSI", value=0.9, confidence=0.0, weight=0.15)
    assert result.weighted_value == 0.0


def test_composite_score_direction():
    buy_score = CompositeScore(
        score=0.5, direction=SignalDirection.BUY, signals=()
    )
    assert buy_score.direction == SignalDirection.BUY

    sell_score = CompositeScore(
        score=-0.5, direction=SignalDirection.SELL, signals=()
    )
    assert sell_score.direction == SignalDirection.SELL


def test_composite_strength_pct():
    score = CompositeScore(score=0.67, direction=SignalDirection.BUY, signals=())
    assert abs(score.strength_pct - 67.0) < 0.001


def test_composite_boundary_suppressed():
    score = CompositeScore(
        score=0.1, direction=SignalDirection.HOLD, signals=(), boundary_suppressed=True
    )
    assert score.boundary_suppressed is True
