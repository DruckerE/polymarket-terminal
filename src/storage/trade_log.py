"""CSV trade persistence for logging all executed trades."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.models.position import Trade

TRADE_LOG_HEADERS = [
    "timestamp",
    "trade_id",
    "market_id",
    "side",
    "outcome",
    "price",
    "size",
    "notional",
    "is_paper",
]


class TradeLog:
    """Persists trades to CSV file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("trades.csv")
        self._ensure_headers()

    def log_trade(self, trade: Trade) -> None:
        """Append a trade to the CSV log."""
        with open(self._path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.fromtimestamp(trade.timestamp).isoformat(),
                trade.trade_id,
                trade.market_id,
                trade.side.value,
                trade.outcome.value,
                f"{trade.price:.4f}",
                f"{trade.size:.2f}",
                f"{trade.notional:.4f}",
                str(trade.is_paper),
            ])

    def read_trades(self) -> list[dict]:
        """Read all trades from the log."""
        if not self._path.exists():
            return []

        trades: list[dict] = []
        with open(self._path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(dict(row))
        return trades

    def _ensure_headers(self) -> None:
        if not self._path.exists():
            with open(self._path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(TRADE_LOG_HEADERS)
