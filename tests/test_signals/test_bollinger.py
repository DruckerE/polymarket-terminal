"""Tests for Bollinger Bands signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.bollinger import BollingerSignal


def test_bollinger_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = BollingerSignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_bollinger_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(
        market=market,
        candles=tuple(sample_candles),
        last_price=sample_candles[-1].close,
    )
    signal = BollingerSignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert result.name == "BB"


def test_bollinger_weight():
    signal = BollingerSignal()
    assert signal.weight == 0.10
