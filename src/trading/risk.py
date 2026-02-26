"""Risk management: Kelly Criterion, position limits, max drawdown."""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.config.settings import TradingSettings
from src.models.position import PnLSnapshot, Position


@dataclass(frozen=True)
class PositionSizing:
    """Result of position sizing calculation."""

    size: float
    kelly_full: float
    kelly_fraction: float
    max_allowed: float
    reason: str


def kelly_criterion(
    win_prob: float,
    win_return: float,
    loss_return: float,
    fraction: float = 0.25,
) -> float:
    """Calculate Kelly Criterion position size.

    Args:
        win_prob: Probability of winning (0-1)
        win_return: Return on win (e.g., 0.5 for 50% return)
        loss_return: Loss on loss (e.g., 1.0 for total loss)
        fraction: Kelly fraction (0.25 = quarter Kelly)

    Returns:
        Fraction of bankroll to bet (0-1)
    """
    if win_prob <= 0 or win_prob >= 1:
        return 0.0
    if win_return <= 0 or loss_return <= 0:
        return 0.0

    kelly = (win_prob * win_return - (1 - win_prob) * loss_return) / win_return
    kelly = max(0.0, kelly)
    return kelly * fraction


def calculate_position_size(
    score: float,
    price: float,
    equity: float,
    settings: TradingSettings,
    open_positions: int = 0,
) -> PositionSizing:
    """Calculate position size based on composite score and risk limits."""
    if open_positions >= settings.max_positions:
        return PositionSizing(
            size=0.0,
            kelly_full=0.0,
            kelly_fraction=0.0,
            max_allowed=0.0,
            reason=f"Max positions ({settings.max_positions}) reached",
        )

    win_prob = 0.5 + abs(score) * 0.3
    win_prob = min(0.8, max(0.2, win_prob))

    if price <= 0 or price >= 1:
        return PositionSizing(
            size=0.0, kelly_full=0.0, kelly_fraction=0.0, max_allowed=0.0, reason="Invalid price"
        )

    win_return = (1.0 - price) / price
    loss_return = 1.0

    full_kelly = kelly_criterion(win_prob, win_return, loss_return, fraction=1.0)
    fractional_kelly = full_kelly * settings.kelly_fraction

    max_bet_pct = settings.max_position_pct
    bet_pct = min(fractional_kelly, max_bet_pct)

    dollar_amount = equity * bet_pct
    size = math.floor(dollar_amount / price) if price > 0 else 0

    return PositionSizing(
        size=float(max(0, size)),
        kelly_full=full_kelly,
        kelly_fraction=fractional_kelly,
        max_allowed=equity * max_bet_pct,
        reason="OK" if size > 0 else "Position too small",
    )


def check_drawdown_circuit_breaker(
    current_equity: float,
    peak_equity: float,
    max_drawdown_pct: float,
) -> bool:
    """Returns True if circuit breaker should trigger (halt trading)."""
    if peak_equity <= 0:
        return False
    drawdown = (peak_equity - current_equity) / peak_equity
    return drawdown >= max_drawdown_pct


def calculate_drawdown(equity_history: list[float]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if len(equity_history) < 2:
        return 0.0

    peak = equity_history[0]
    max_dd = 0.0

    for equity in equity_history:
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    return max_dd
