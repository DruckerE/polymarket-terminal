"""On-Balance Volume trend signal (weight 0.10)."""

from __future__ import annotations

import numpy as np

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal


class OBVSignal(Signal):
    """On-Balance Volume measures buying/selling pressure via cumulative volume.

    Rising OBV with rising price = bullish confirmation.
    Falling OBV with rising price = bearish divergence.
    """

    @property
    def name(self) -> str:
        return "OBV"

    @property
    def weight(self) -> float:
        return 0.10

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < 5:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        obv_values = [0.0]
        for i in range(1, len(candles)):
            if candles[i].close > candles[i - 1].close:
                obv_values.append(obv_values[-1] + candles[i].volume)
            elif candles[i].close < candles[i - 1].close:
                obv_values.append(obv_values[-1] - candles[i].volume)
            else:
                obv_values.append(obv_values[-1])

        obv = np.array(obv_values)

        lookback = min(10, len(obv))
        recent_obv = obv[-lookback:]

        if len(recent_obv) < 2:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        x = np.arange(len(recent_obv))
        coeffs = np.polyfit(x, recent_obv, 1)
        slope = coeffs[0]

        max_slope = max(abs(slope), 1.0)
        value = self._clamp(slope / max_slope)

        confidence = min(1.0, len(candles) / 15.0)

        return SignalResult(name=self.name, value=value, confidence=confidence, weight=self.weight)
