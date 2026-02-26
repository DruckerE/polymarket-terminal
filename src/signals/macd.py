"""MACD signal with fast params 5/13/4 (weight 0.10)."""

from __future__ import annotations

import numpy as np

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal

FAST_PERIOD = 5
SLOW_PERIOD = 13
SIGNAL_PERIOD = 4


def _ema(values: np.ndarray, period: int) -> np.ndarray:
    """Exponential moving average."""
    alpha = 2.0 / (period + 1)
    result = np.empty_like(values)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
    return result


class MACDSignal(Signal):
    """MACD with fast parameters (5/13/4) for short-timeframe trading.

    MACD crossing above signal line = bullish.
    MACD crossing below signal line = bearish.
    """

    @property
    def name(self) -> str:
        return "MACD"

    @property
    def weight(self) -> float:
        return 0.10

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < SLOW_PERIOD + SIGNAL_PERIOD:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        closes = np.array([c.close for c in candles])

        fast_ema = _ema(closes, FAST_PERIOD)
        slow_ema = _ema(closes, SLOW_PERIOD)

        macd_line = fast_ema - slow_ema
        signal_line = _ema(macd_line, SIGNAL_PERIOD)

        histogram = macd_line - signal_line
        current_hist = float(histogram[-1])
        prev_hist = float(histogram[-2])

        max_hist = float(np.max(np.abs(histogram[-20:]))) if len(histogram) >= 20 else 0.05
        if max_hist == 0:
            max_hist = 0.05

        value = self._clamp(current_hist / max_hist)

        crossover_bonus = 0.0
        if prev_hist <= 0 < current_hist:
            crossover_bonus = 0.3
        elif prev_hist >= 0 > current_hist:
            crossover_bonus = -0.3
        value = self._clamp(value + crossover_bonus)

        confidence = min(1.0, len(candles) / (SLOW_PERIOD * 2))

        return SignalResult(name=self.name, value=value, confidence=confidence, weight=self.weight)
