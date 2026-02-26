"""Order Book Imbalance signal (weight 0.30)."""

from __future__ import annotations

from src.data.market_cache import MarketState
from src.models.signal import SignalResult
from src.signals.base import Signal


class OBISignal(Signal):
    """Measures bid vs ask depth imbalance across top 5 levels.

    Positive imbalance = more buying interest = bullish.
    """

    @property
    def name(self) -> str:
        return "OBI"

    @property
    def weight(self) -> float:
        return 0.30

    def calculate(self, state: MarketState) -> SignalResult:
        if not state.orderbook or (not state.orderbook.bids and not state.orderbook.asks):
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        book = state.orderbook
        bid_depth = sum(level.size for level in book.bids[:5])
        ask_depth = sum(level.size for level in book.asks[:5])
        total = bid_depth + ask_depth

        if total == 0:
            return SignalResult(name=self.name, value=0.0, confidence=0.0, weight=self.weight)

        imbalance = (bid_depth - ask_depth) / total
        value = self._clamp(imbalance)

        num_levels = min(len(book.bids), len(book.asks), 5)
        confidence = min(1.0, num_levels / 3.0) * min(1.0, total / 100.0)

        return SignalResult(name=self.name, value=value, confidence=confidence, weight=self.weight)
