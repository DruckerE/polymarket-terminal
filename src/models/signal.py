"""Signal result and composite score frozen dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalDirection(Enum):
    """Trading direction from signal analysis."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class SignalResult:
    """Result from a single signal calculation."""

    name: str
    value: float  # Raw signal value (-1.0 to 1.0)
    confidence: float  # 0.0 to 1.0
    weight: float

    @property
    def weighted_value(self) -> float:
        return self.value * self.confidence * self.weight


@dataclass(frozen=True)
class CompositeScore:
    """Aggregated score from all signals."""

    score: float  # Weighted composite (-1.0 to 1.0)
    direction: SignalDirection
    signals: tuple[SignalResult, ...]
    boundary_suppressed: bool = False
    timestamp: float = 0.0

    @property
    def strength_pct(self) -> float:
        """Score as a percentage (0-100)."""
        return abs(self.score) * 100.0
