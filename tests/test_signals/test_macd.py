"""Tests for MACD signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.macd import MACDSignal


def test_macd_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = MACDSignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_macd_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=tuple(sample_candles))
    signal = MACDSignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert result.name == "MACD"


def test_macd_weight():
    signal = MACDSignal()
    assert signal.weight == 0.10
