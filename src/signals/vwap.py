"""VWAP deviation signal (weight 0.20)."""

from __future__ import annotations

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal


class VWAPSignal(Signal):
    """Volume-Weighted Average Price deviation.

    Price below VWAP = bullish (undervalued), above = bearish (overvalued).
    """

    @property
    def name(self) -> str:
        return "VWAP"

    @property
    def weight(self) -> float:
        return 0.20

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < 2:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        total_volume = 0.0
        total_tp_volume = 0.0

        for candle in candles:
            tp = candle.typical_price
            total_tp_volume += tp * candle.volume
            total_volume += candle.volume

        if total_volume == 0:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        vwap = total_tp_volume / total_volume
        current_price = state.last_price or candles[-1].close

        deviation = current_price - vwap
        max_deviation = 0.1
        normalized = self._clamp(-(deviation / max_deviation))

        confidence = min(1.0, len(candles) / 10.0) * min(1.0, total_volume / 50.0)

        return SignalResult(
            name=self.name, value=normalized, confidence=min(confidence, 1.0), weight=self.weight
        )
