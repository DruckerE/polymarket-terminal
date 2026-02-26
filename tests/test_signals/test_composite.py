"""Tests for composite signal scoring engine."""

import time

from src.data.market_cache import MarketState
from src.models.market import Market, Outcome
from src.models.orderbook import OrderBook, OrderLevel
from src.models.signal import SignalDirection
from src.signals.composite import CompositeEngine


def test_composite_returns_hold_with_no_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market)
    engine = CompositeEngine()
    score = engine.calculate(state)
    assert score.direction == SignalDirection.HOLD
    assert len(score.signals) == 7


def test_composite_with_full_data(sample_candles, sample_orderbook):
    market = Market(
        condition_id="test",
        question="Test?",
        slug="test",
        outcomes=(
            Outcome(token_id="tok-yes", label="Yes", price=0.52),
            Outcome(token_id="tok-no", label="No", price=0.48),
        ),
    )
    state = MarketState(
        market=market,
        orderbook=sample_orderbook,
        candles=tuple(sample_candles),
        last_price=0.52,
    )
    engine = CompositeEngine()
    score = engine.calculate(state)
    assert -1.0 <= score.score <= 1.0
    assert score.direction in (SignalDirection.BUY, SignalDirection.SELL, SignalDirection.HOLD)
    assert len(score.signals) == 7
    assert score.timestamp > 0


def test_composite_boundary_suppression(sample_candles, sample_orderbook):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(
        market=market,
        orderbook=sample_orderbook,
        candles=tuple(sample_candles),
        last_price=0.02,
    )
    engine = CompositeEngine()
    score = engine.calculate(state)
    assert score.boundary_suppressed is True


def test_composite_signal_weights_sum():
    engine = CompositeEngine()
    total = sum(s.weight for s in engine._signals)
    assert abs(total - 1.0) < 0.001
