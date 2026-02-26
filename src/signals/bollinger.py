"""Bollinger Bands %B signal (weight 0.10)."""

from __future__ import annotations

import numpy as np

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal

BB_PERIOD = 20
BB_STD_DEV = 2.0


class BollingerSignal(Signal):
    """Bollinger Bands %B - excellent for bounded [0,1] prediction market prices.

    %B < 0 = below lower band (oversold/bullish)
    %B > 1 = above upper band (overbought/bearish)
    %B ~ 0.5 = at middle band (neutral)
    """

    @property
    def name(self) -> str:
        return "BB"

    @property
    def weight(self) -> float:
        return 0.10

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < BB_PERIOD:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        closes = np.array([c.close for c in candles[-BB_PERIOD:]])

        sma = float(np.mean(closes))
        std = float(np.std(closes, ddof=1))

        if std == 0:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        upper_band = sma + BB_STD_DEV * std
        lower_band = sma - BB_STD_DEV * std
        band_width = upper_band - lower_band

        if band_width == 0:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        current_price = state.last_price or candles[-1].close
        percent_b = (current_price - lower_band) / band_width

        if percent_b < 0.2:
            value = (0.2 - percent_b) / 0.2
        elif percent_b > 0.8:
            value = -(percent_b - 0.8) / 0.2
        else:
            value = 0.0

        value = self._clamp(value)
        confidence = min(1.0, len(candles) / (BB_PERIOD * 1.5))

        return SignalResult(name=self.name, value=value, confidence=confidence, weight=self.weight)
