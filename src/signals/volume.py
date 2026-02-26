"""Volume spike/confirmation signal (weight 0.05)."""

from __future__ import annotations

import numpy as np

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal

VOLUME_SPIKE_THRESHOLD = 2.0


class VolumeSignal(Signal):
    """Volume spike detection and trend confirmation.

    Volume spike with bullish candle = strong buy confirmation.
    Volume spike with bearish candle = strong sell confirmation.
    Normal volume = neutral.
    """

    @property
    def name(self) -> str:
        return "VOL"

    @property
    def weight(self) -> float:
        return 0.05

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < 5:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        volumes = np.array([c.volume for c in candles])
        avg_volume = float(np.mean(volumes[:-1]))

        if avg_volume == 0:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume

        latest = candles[-1]
        is_spike = volume_ratio >= VOLUME_SPIKE_THRESHOLD

        if is_spike:
            if latest.is_bullish:
                value = min(1.0, (volume_ratio - 1.0) / 3.0)
            else:
                value = -min(1.0, (volume_ratio - 1.0) / 3.0)
        else:
            if latest.is_bullish:
                value = 0.1 * (volume_ratio - 1.0)
            else:
                value = -0.1 * (volume_ratio - 1.0)

        value = self._clamp(value)
        confidence = min(1.0, len(candles) / 10.0) * min(1.0, volume_ratio / 2.0)

        return SignalResult(
            name=self.name, value=value, confidence=min(confidence, 1.0), weight=self.weight
        )
