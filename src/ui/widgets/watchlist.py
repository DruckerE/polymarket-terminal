"""Multi-market watchlist DataTable widget."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import DataTable

from src.data.market_cache import MarketCache, MarketState


class WatchlistPanel(Container):
    """Watchlist showing tracked markets with prices and changes."""

    DEFAULT_CSS = """
    WatchlistPanel {
        width: 1fr;
        min-width: 28;
        height: 100%;
        border: solid #333333;
        background: #000000;
    }
    """

    def __init__(self, cache: MarketCache, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cache = cache

    def compose(self):
        table = DataTable(id="watchlist-table")
        table.add_columns("Market", "Price", "Chg")
        table.cursor_type = "row"
        yield table

    def update_watchlist(self) -> None:
        try:
            table = self.query_one("#watchlist-table", DataTable)
        except Exception:
            return

        table.clear()
        for state in self._cache.all_states():
            name = state.market.question[:20]
            price = f"${state.last_price:.2f}" if state.last_price else "--"
            change = self._calc_change(state)
            table.add_row(name, price, change)

    def _calc_change(self, state: MarketState) -> str:
        if len(state.candles) < 2:
            return "--"
        prev = state.candles[-2].close
        curr = state.last_price or state.candles[-1].close
        if prev == 0:
            return "--"
        pct = ((curr - prev) / prev) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}%"
