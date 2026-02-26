"""Tests for tick-to-candle aggregation."""

import time

from src.data.candle_aggregator import CandleAggregator
from src.models.candle import Candle


def test_first_tick_starts_candle():
    agg = CandleAggregator(interval=300)
    result = agg.add_tick(0.50, size=10.0, timestamp=1000.0)
    assert result is None  # No completed candle yet
    assert agg.current_candle_start > 0


def test_candle_completes_on_interval():
    agg = CandleAggregator(interval=10)
    agg.add_tick(0.50, size=5.0, timestamp=100.0)
    agg.add_tick(0.55, size=3.0, timestamp=105.0)

    result = agg.add_tick(0.52, size=4.0, timestamp=111.0)
    assert result is not None
    assert result.open == 0.50
    assert result.high == 0.55
    assert result.low == 0.50
    assert result.close == 0.55
    assert result.trade_count == 2


def test_ohlcv_values():
    agg = CandleAggregator(interval=10)
    agg.add_tick(0.50, size=1.0, timestamp=100.0)
    agg.add_tick(0.60, size=2.0, timestamp=103.0)
    agg.add_tick(0.45, size=3.0, timestamp=106.0)
    agg.add_tick(0.55, size=4.0, timestamp=109.0)

    result = agg.add_tick(0.52, size=1.0, timestamp=111.0)
    assert result is not None
    assert result.open == 0.50
    assert result.high == 0.60
    assert result.low == 0.45
    assert result.close == 0.55
    assert result.volume == 10.0


def test_force_close():
    agg = CandleAggregator(interval=300)
    agg.add_tick(0.50, size=1.0, timestamp=1000.0)
    agg.add_tick(0.55, size=2.0, timestamp=1010.0)

    result = agg.force_close()
    assert result is not None
    assert result.open == 0.50
    assert result.close == 0.55


def test_candles_accumulate():
    agg = CandleAggregator(interval=10)
    for i in range(5):
        agg.add_tick(0.50 + i * 0.01, size=1.0, timestamp=100 + i * 11)

    assert len(agg.candles) >= 3


def test_load_historical():
    agg = CandleAggregator()
    historical = [
        Candle(timestamp=100, open=0.50, high=0.55, low=0.48, close=0.53, volume=100),
        Candle(timestamp=400, open=0.53, high=0.56, low=0.51, close=0.54, volume=80),
    ]
    agg.load_historical(historical)
    assert len(agg.candles) == 2
