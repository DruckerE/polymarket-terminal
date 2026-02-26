"""Tests for Volume signal."""

from src.data.market_cache import MarketState
from src.models.market import Market
from src.signals.volume import VolumeSignal


def test_volume_insufficient_data():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=())
    signal = VolumeSignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_volume_with_candles(sample_candles):
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market, candles=tuple(sample_candles))
    signal = VolumeSignal()
    result = signal.calculate(state)
    assert -1.0 <= result.value <= 1.0
    assert result.name == "VOL"


def test_volume_weight():
    signal = VolumeSignal()
    assert signal.weight == 0.05
