"""Tests for On-Balance Volume signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.obv import OBVSignal


def test_obv_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = OBVSignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_obv_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=tuple(sample_candles))
    signal = OBVSignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert result.name == "OBV"


def test_obv_weight():
    signal = OBVSignal()
    assert signal.weight == 0.10
