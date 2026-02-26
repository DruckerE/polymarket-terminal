"""CSV logger for scalp trades — every entry and exit gets a row."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from src.trading.scalper import ScalpResult

SCALP_LOG_HEADERS = [
    "timestamp",
    "slug",
    "side",
    "entry_price",
    "exit_price",
    "shares",
    "pnl",
    "hold_seconds",
    "exit_reason",
    "balance",
    "trade_num",
]


class ScalpCsvLogger:
    """Appends each completed scalp trade to a CSV file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("scalp_trades.csv")
        self._ensure_headers()

    def log(
        self,
        result: ScalpResult,
        slug: str,
        balance: float,
        trade_num: int,
    ) -> None:
        """Append one scalp result row."""
        now = datetime.now(tz=timezone.utc).isoformat()
        row = [
            now,
            slug,
            result.side,
            f"{result.entry_price:.4f}",
            f"{result.exit_price:.4f}",
            f"{result.shares:.2f}",
            f"{result.pnl:+.4f}",
            f"{result.hold_time:.1f}",
            result.exit_reason,
            f"{balance:.2f}",
            str(trade_num),
        ]
        with open(self._path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def read_all(self) -> list[dict]:
        """Read back all logged trades."""
        if not self._path.exists():
            return []
        trades: list[dict] = []
        with open(self._path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(dict(row))
        return trades

    def _ensure_headers(self) -> None:
        """Write header row if file doesn't exist yet (atomic creation)."""
        try:
            with open(self._path, "x", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(SCALP_LOG_HEADERS)
        except FileExistsError:
            pass
