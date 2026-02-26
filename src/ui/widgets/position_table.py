"""Open positions DataTable widget."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import DataTable

from src.models.position import Position


class PositionTable(Container):
    """DataTable showing all open positions with P&L."""

    DEFAULT_CSS = """
    PositionTable {
        height: auto;
        max-height: 8;
        border: solid #333333;
        background: #000000;
    }
    """

    def compose(self):
        table = DataTable(id="pos-table")
        table.add_columns("Market", "Side", "Size", "Entry", "Current", "P&L")
        table.cursor_type = "row"
        yield table

    def update_positions(self, positions: dict[str, Position]) -> None:
        try:
            table = self.query_one("#pos-table", DataTable)
        except Exception:
            return

        table.clear()
        for market_id, pos in positions.items():
            pnl = pos.unrealized_pnl
            table.add_row(
                market_id[:15],
                pos.outcome.value,
                f"{pos.size:.0f}",
                f"${pos.avg_entry_price:.3f}",
                f"${pos.current_price:.3f}",
                f"${pnl:+.2f}",
            )
