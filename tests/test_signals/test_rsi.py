"""Tests for RSI signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.rsi import RSISignal


def test_rsi_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = RSISignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_rsi_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=tuple(sample_candles))
    signal = RSISignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.name == "RSI"


def test_rsi_weight():
    signal = RSISignal()
    assert signal.weight == 0.15
