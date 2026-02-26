"""Position, Trade, and PnLSnapshot frozen dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    """Trade side."""

    BUY = "BUY"
    SELL = "SELL"


class OutcomeType(Enum):
    """Outcome type for the position."""

    YES = "YES"
    NO = "NO"


@dataclass(frozen=True)
class Trade:
    """A single executed trade."""

    trade_id: str
    market_id: str
    token_id: str
    side: Side
    outcome: OutcomeType
    price: float
    size: float
    timestamp: float
    is_paper: bool = True

    @property
    def notional(self) -> float:
        return self.price * self.size


@dataclass(frozen=True)
class Position:
    """An open position in a market."""

    market_id: str
    token_id: str
    outcome: OutcomeType
    size: float
    avg_entry_price: float
    current_price: float = 0.0
    stop_loss: float | None = None

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_entry_price) * self.size

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_entry_price == 0:
            return 0.0
        return (self.current_price - self.avg_entry_price) / self.avg_entry_price * 100.0

    @property
    def notional(self) -> float:
        return self.current_price * self.size

    @property
    def cost_basis(self) -> float:
        return self.avg_entry_price * self.size


@dataclass(frozen=True)
class PnLSnapshot:
    """Point-in-time P&L snapshot for equity curve."""

    timestamp: float
    realized_pnl: float
    unrealized_pnl: float
    total_equity: float
    win_rate: float = 0.0
    total_trades: int = 0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    trade_history: tuple[Trade, ...] = field(default_factory=tuple)

    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl
