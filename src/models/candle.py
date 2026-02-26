"""Candle (OHLCV) frozen dataclass for 5-minute price aggregation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    """A single OHLCV candlestick."""

    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int = 0

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open

    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3.0
