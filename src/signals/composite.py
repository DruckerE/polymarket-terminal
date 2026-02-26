"""Weighted composite signal scoring engine."""

from __future__ import annotations

import time

from src.config.constants import BUY_THRESHOLD, SELL_THRESHOLD
from src.config.settings import SignalWeights
from src.data.market_cache import MarketState
from src.models.signal import CompositeScore, SignalDirection, SignalResult
from src.signals.base import Signal
from src.signals.bollinger import BollingerSignal
from src.signals.boundary import boundary_suppression_factor, is_at_boundary
from src.signals.macd import MACDSignal
from src.signals.obi import OBISignal
from src.signals.obv import OBVSignal
from src.signals.rsi import RSISignal
from src.signals.volume import VolumeSignal
from src.signals.vwap import VWAPSignal


class CompositeEngine:
    """Aggregates all signals into a single composite score."""

    def __init__(self, weights: SignalWeights | None = None) -> None:
        self._weights = weights or SignalWeights()
        self._signals: tuple[Signal, ...] = (
            OBISignal(),
            VWAPSignal(),
            RSISignal(),
            MACDSignal(),
            BollingerSignal(),
            OBVSignal(),
            VolumeSignal(),
        )

    def calculate(self, state: MarketState) -> CompositeScore:
        """Calculate composite score from all signals."""
        results: list[SignalResult] = []
        for signal in self._signals:
            result = signal.calculate(state)
            weight = self._get_weight(signal.name)
            results.append(
                SignalResult(
                    name=result.name,
                    value=result.value,
                    confidence=result.confidence,
                    weight=weight,
                )
            )

        weighted_sum = sum(r.weighted_value for r in results)
        total_weight = sum(r.weight * r.confidence for r in results)
        raw_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        price = state.last_price
        suppressed = is_at_boundary(price) if price > 0 else False
        if suppressed:
            factor = boundary_suppression_factor(price)
            raw_score *= factor

        score = max(-1.0, min(1.0, raw_score))

        if score > BUY_THRESHOLD:
            direction = SignalDirection.BUY
        elif score < SELL_THRESHOLD:
            direction = SignalDirection.SELL
        else:
            direction = SignalDirection.HOLD

        return CompositeScore(
            score=score,
            direction=direction,
            signals=tuple(results),
            boundary_suppressed=suppressed,
            timestamp=time.time(),
        )

    def _get_weight(self, signal_name: str) -> float:
        weight_map = {
            "OBI": self._weights.obi,
            "VWAP": self._weights.vwap,
            "RSI": self._weights.rsi,
            "MACD": self._weights.macd,
            "BB": self._weights.bollinger,
            "OBV": self._weights.obv,
            "VOL": self._weights.volume,
        }
        return weight_map.get(signal_name, 0.05)
