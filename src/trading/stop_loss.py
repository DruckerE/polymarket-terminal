"""ATR-based dynamic stop-loss calculation."""

from __future__ import annotations

from src.models.candle import Candle
from src.models.position import Position


def calculate_atr(candles: tuple[Candle, ...] | list[Candle], period: int = 14) -> float:
    """Calculate Average True Range from candles."""
    if len(candles) < 2:
        return 0.0

    recent = list(candles[-period - 1 :])
    if len(recent) < 2:
        return 0.0

    true_ranges: list[float] = []
    for i in range(1, len(recent)):
        high_low = recent[i].high - recent[i].low
        high_close = abs(recent[i].high - recent[i - 1].close)
        low_close = abs(recent[i].low - recent[i - 1].close)
        true_ranges.append(max(high_low, high_close, low_close))

    if not true_ranges:
        return 0.0

    return sum(true_ranges) / len(true_ranges)


def calculate_stop_loss(
    position: Position,
    candles: tuple[Candle, ...] | list[Candle],
    atr_multiplier: float = 2.0,
) -> float:
    """Calculate dynamic stop-loss price based on ATR.

    For long positions: entry_price - (ATR * multiplier)
    Clamped to [0, 1] for prediction markets.
    """
    atr = calculate_atr(candles)
    if atr == 0:
        return max(0.0, position.avg_entry_price - 0.05)

    stop = position.avg_entry_price - (atr * atr_multiplier)
    return max(0.0, min(1.0, stop))


def should_stop_out(position: Position, current_price: float) -> bool:
    """Check if position should be stopped out."""
    if position.stop_loss is None:
        return False
    return current_price <= position.stop_loss
