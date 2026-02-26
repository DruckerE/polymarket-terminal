"""Position state tracking and P&L calculation."""

from __future__ import annotations

import time

from src.models.position import OutcomeType, PnLSnapshot, Position, Side, Trade


class PositionTracker:
    """Tracks open positions and calculates P&L."""

    def __init__(self, starting_equity: float = 1000.0) -> None:
        self._positions: dict[str, Position] = {}
        self._closed_trades: list[Trade] = []
        self._realized_pnl = 0.0
        self._starting_equity = starting_equity
        self._peak_equity = starting_equity
        self._wins = 0
        self._losses = 0

    @property
    def positions(self) -> dict[str, Position]:
        return dict(self._positions)

    @property
    def open_count(self) -> int:
        return len(self._positions)

    @property
    def realized_pnl(self) -> float:
        return self._realized_pnl

    def process_trade(self, trade: Trade) -> None:
        """Process a new trade and update positions."""
        key = f"{trade.market_id}:{trade.outcome.value}"

        if trade.side == Side.BUY:
            self._open_or_add(key, trade)
        else:
            self._close_or_reduce(key, trade)

    def update_prices(self, market_id: str, yes_price: float, no_price: float) -> None:
        """Update current prices for P&L calculation."""
        for key, pos in list(self._positions.items()):
            if pos.market_id == market_id:
                price = yes_price if pos.outcome == OutcomeType.YES else no_price
                self._positions[key] = Position(
                    market_id=pos.market_id,
                    token_id=pos.token_id,
                    outcome=pos.outcome,
                    size=pos.size,
                    avg_entry_price=pos.avg_entry_price,
                    current_price=price,
                    stop_loss=pos.stop_loss,
                )

    def snapshot(self, balance: float) -> PnLSnapshot:
        """Create a P&L snapshot."""
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        total_equity = balance + unrealized
        self._peak_equity = max(self._peak_equity, total_equity)

        total_trades = self._wins + self._losses
        win_rate = (self._wins / total_trades * 100) if total_trades > 0 else 0.0
        max_dd = (self._peak_equity - total_equity) if total_equity < self._peak_equity else 0.0

        return PnLSnapshot(
            timestamp=time.time(),
            realized_pnl=self._realized_pnl,
            unrealized_pnl=unrealized,
            total_equity=total_equity,
            win_rate=win_rate,
            total_trades=total_trades,
            max_drawdown=max_dd,
        )

    def _open_or_add(self, key: str, trade: Trade) -> None:
        existing = self._positions.get(key)
        if existing:
            total_size = existing.size + trade.size
            avg_price = (
                (existing.avg_entry_price * existing.size + trade.price * trade.size) / total_size
            )
            self._positions[key] = Position(
                market_id=trade.market_id,
                token_id=trade.token_id,
                outcome=trade.outcome,
                size=total_size,
                avg_entry_price=avg_price,
                current_price=trade.price,
                stop_loss=existing.stop_loss,
            )
        else:
            self._positions[key] = Position(
                market_id=trade.market_id,
                token_id=trade.token_id,
                outcome=trade.outcome,
                size=trade.size,
                avg_entry_price=trade.price,
                current_price=trade.price,
            )

    def _close_or_reduce(self, key: str, trade: Trade) -> None:
        existing = self._positions.get(key)
        if not existing:
            return

        pnl = (trade.price - existing.avg_entry_price) * min(trade.size, existing.size)
        self._realized_pnl += pnl

        if pnl >= 0:
            self._wins += 1
        else:
            self._losses += 1

        self._closed_trades.append(trade)

        remaining = existing.size - trade.size
        if remaining <= 0:
            del self._positions[key]
        else:
            self._positions[key] = Position(
                market_id=existing.market_id,
                token_id=existing.token_id,
                outcome=existing.outcome,
                size=remaining,
                avg_entry_price=existing.avg_entry_price,
                current_price=trade.price,
                stop_loss=existing.stop_loss,
            )
