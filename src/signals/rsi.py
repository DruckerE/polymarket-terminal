"""RSI signal - 9-period fast RSI (weight 0.15)."""

from __future__ import annotations

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal

RSI_PERIOD = 9
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0


class RSISignal(Signal):
    """9-period RSI optimized for 5-minute candles.

    RSI < 30 = oversold (bullish), RSI > 70 = overbought (bearish).
    """

    @property
    def name(self) -> str:
        return "RSI"

    @property
    def weight(self) -> float:
        return 0.15

    def calculate(self, state: MarketState) -> SignalResult:
        candles = state.candles
        if len(candles) < RSI_PERIOD + 1:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        closes = [c.close for c in candles[-(RSI_PERIOD + 1) :]]
        gains: list[float] = []
        losses: list[float] = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))

        avg_gain = sum(gains) / RSI_PERIOD
        avg_loss = sum(losses) / RSI_PERIOD

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))

        if rsi < RSI_OVERSOLD:
            value = (RSI_OVERSOLD - rsi) / RSI_OVERSOLD
        elif rsi > RSI_OVERBOUGHT:
            value = -(rsi - RSI_OVERBOUGHT) / (100.0 - RSI_OVERBOUGHT)
        else:
            value = 0.0

        value = self._clamp(value)
        confidence = min(1.0, len(candles) / (RSI_PERIOD * 2))

        return SignalResult(name=self.name, value=value, confidence=confidence, weight=self.weight)
