"""Tick-to-candle aggregation for building 5-minute OHLCV candles."""

from __future__ import annotations

import time
from dataclasses import dataclass

from src.config.constants import CANDLE_INTERVAL_SECONDS
from src.models.candle import Candle


@dataclass
class _CandleBuilder:
    """Mutable builder for in-progress candle (internal only)."""

    start_time: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int


class CandleAggregator:
    """Aggregates tick data into fixed-interval OHLCV candles."""

    def __init__(self, interval: int = CANDLE_INTERVAL_SECONDS) -> None:
        self._interval = interval
        self._current: _CandleBuilder | None = None
        self._candles: list[Candle] = []

    @property
    def candles(self) -> tuple[Candle, ...]:
        return tuple(self._candles)

    @property
    def current_candle_start(self) -> float:
        if self._current:
            return self._current.start_time
        return 0.0

    @property
    def seconds_remaining(self) -> float:
        if not self._current:
            return float(self._interval)
        elapsed = time.time() - self._current.start_time
        return max(0.0, self._interval - elapsed)

    def add_tick(self, price: float, size: float = 1.0, timestamp: float | None = None) -> Candle | None:
        """Process a tick. Returns a completed Candle if interval elapsed."""
        ts = timestamp or time.time()
        completed = None

        if self._current is None:
            self._start_new_candle(price, size, ts)
            return None

        elapsed = ts - self._current.start_time
        if elapsed >= self._interval:
            completed = self._finalize_candle()
            self._start_new_candle(price, size, ts)
        else:
            self._update_candle(price, size)

        return completed

    def force_close(self) -> Candle | None:
        """Force-close the current candle."""
        if self._current is None:
            return None
        return self._finalize_candle()

    def load_historical(self, candles: list[Candle]) -> None:
        """Load historical candles into the aggregator."""
        self._candles = list(candles)

    def _start_new_candle(self, price: float, size: float, ts: float) -> None:
        interval_start = ts - (ts % self._interval)
        self._current = _CandleBuilder(
            start_time=interval_start,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=size,
            trade_count=1,
        )

    def _update_candle(self, price: float, size: float) -> None:
        if self._current is None:
            return
        self._current.high = max(self._current.high, price)
        self._current.low = min(self._current.low, price)
        self._current.close = price
        self._current.volume += size
        self._current.trade_count += 1

    def _finalize_candle(self) -> Candle:
        if self._current is None:
            raise RuntimeError("No candle to finalize")

        candle = Candle(
            timestamp=self._current.start_time,
            open=self._current.open,
            high=self._current.high,
            low=self._current.low,
            close=self._current.close,
            volume=self._current.volume,
            trade_count=self._current.trade_count,
        )
        self._candles.append(candle)
        self._current = None
        return candle
