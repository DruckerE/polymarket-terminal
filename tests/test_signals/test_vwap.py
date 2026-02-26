"""Tests for VWAP signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.vwap import VWAPSignal


def test_vwap_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = VWAPSignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_vwap_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(
        market=market,
        candles=tuple(sample_candles),
        last_price=sample_candles[-1].close,
    )
    signal = VWAPSignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert result.name == "VWAP"


def test_vwap_weight():
    signal = VWAPSignal()
    assert signal.weight == 0.20
