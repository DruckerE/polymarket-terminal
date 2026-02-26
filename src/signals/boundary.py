"""Price boundary suppression for prediction market prices near 0 or 1."""

from __future__ import annotations

from src.config.constants import BOUNDARY_HIGH, BOUNDARY_LOW


def boundary_suppression_factor(price: float) -> float:
    """Calculate suppression factor for prices near boundaries.

    Returns a multiplier in [0.0, 1.0]:
    - 1.0 = no suppression (price in normal range)
    - 0.0 = full suppression (price at boundary)

    Prediction market prices near 0 or 1 behave differently
    from mid-range prices. Traditional technical signals
    become unreliable at extremes.
    """
    if price <= 0 or price >= 1:
        return 0.0

    if price < BOUNDARY_LOW:
        return price / BOUNDARY_LOW
    elif price > BOUNDARY_HIGH:
        return (1.0 - price) / (1.0 - BOUNDARY_HIGH)

    return 1.0


def is_at_boundary(price: float) -> bool:
    """Check if price is at or near a boundary."""
    return price < BOUNDARY_LOW or price > BOUNDARY_HIGH
