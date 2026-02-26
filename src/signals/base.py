"""Abstract base class for all trading signals."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.data.market_cache import MarketState
from src.models.signal import SignalResult


class Signal(ABC):
    """Base class for trading signal calculators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable signal name."""

    @property
    @abstractmethod
    def weight(self) -> float:
        """Default weight in composite scoring."""

    @abstractmethod
    def calculate(self, state: MarketState) -> SignalResult:
        """Calculate signal from current market state.

        Returns a SignalResult with value in [-1.0, 1.0] and confidence in [0.0, 1.0].
        """

    def _clamp(self, value: float, low: float = -1.0, high: float = 1.0) -> float:
        return max(low, min(high, value))
