"""Market search modal screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Static

from src.data.gamma_client import get_active_markets, search_markets_by_query
from src.data.market_cache import MarketCache
from src.models.market import Market


class MarketSearchScreen(ModalScreen):
    """Modal for searching and selecting Polymarket markets."""

    DEFAULT_CSS = """
    MarketSearchScreen {
        align: center middle;
        background: #000000cc;
    }

    #search-container {
        width: 80;
        height: 30;
        border: double #FFB000;
        background: #0A0A0A;
        padding: 1 2;
    }

    #search-title {
        color: #FFB000;
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }

    #search-input {
        margin: 0 0 1 0;
    }

    #search-results {
        height: 1fr;
    }

    #search-close {
        dock: bottom;
        margin: 1 0 0 0;
    }
    """

    class MarketSelected(Message):
        """Posted when a market is selected."""

        def __init__(self, market: Market) -> None:
            self.market = market
            super().__init__()

    def __init__(self, cache: MarketCache, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cache = cache
        self._markets: list[Market] = []

    def compose(self) -> ComposeResult:
        with Container(id="search-container"):
            yield Static("MARKET SEARCH", id="search-title")
            yield Input(placeholder="Search markets...", id="search-input")
            table = DataTable(id="search-results")
            table.add_columns("Market", "Volume", "YES", "NO")
            table.cursor_type = "row"
            yield table
            yield Button("Close [ESC]", id="search-close", variant="default")

    async def on_mount(self) -> None:
        try:
            markets = await get_active_markets(limit=20)
            self._markets = markets
            self._populate_table(markets)
        except Exception as exc:
            self.notify(f"Failed to load markets: {exc}", severity="error")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return

        try:
            markets = await search_markets_by_query(query, limit=20)
            self._markets = markets
            self._populate_table(markets)
        except Exception as exc:
            self.notify(f"Search failed: {exc}", severity="error")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if 0 <= row_idx < len(self._markets):
            market = self._markets[row_idx]
            self._cache.set_market(market)
            self._cache.active_market_id = market.condition_id
            self.dismiss(market)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-close":
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)

    def _populate_table(self, markets: list[Market]) -> None:
        try:
            table = self.query_one("#search-results", DataTable)
        except Exception:
            return

        table.clear()
        for market in markets:
            table.add_row(
                market.question[:40],
                f"${market.volume:,.0f}",
                f"${market.yes_price:.2f}",
                f"${market.no_price:.2f}",
            )
