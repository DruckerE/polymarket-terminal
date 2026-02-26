"""Primary dashboard layout screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical

from src.config.settings import AppSettings
from src.data.market_cache import MarketCache
from src.ui.widgets.arbitrage_alert import ArbitrageAlert
from src.ui.widgets.chart_panel import ChartPanel
from src.ui.widgets.command_input import CommandInput
from src.ui.widgets.header_bar import HeaderBar
from src.ui.widgets.orderbook_panel import OrderBookPanel
from src.ui.widgets.pnl_panel import PnLPanel
from src.ui.widgets.position_table import PositionTable
from src.ui.widgets.signal_panel import SignalPanel
from src.ui.widgets.status_bar import StatusBar
from src.ui.widgets.trade_tape import TradeTape
from src.ui.widgets.watchlist import WatchlistPanel


class MainScreen(Container):
    """Primary Bloomberg-style dashboard layout."""

    DEFAULT_CSS = """
    MainScreen {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, cache: MarketCache, settings: AppSettings, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cache = cache
        self._settings = settings
        self._header = HeaderBar()
        self._chart = ChartPanel()
        self._orderbook = OrderBookPanel()
        self._signals = SignalPanel()
        self._watchlist = WatchlistPanel(cache)
        self._tape = TradeTape()
        self._pnl = PnLPanel()
        self._positions = PositionTable()
        self._arb_alert = ArbitrageAlert()
        self._status = StatusBar()
        self._command = CommandInput()

    def compose(self) -> ComposeResult:
        yield self._header

        with Horizontal(id="top-row"):
            yield self._chart
            yield self._orderbook

        with Horizontal(id="mid-row"):
            yield self._signals
            yield self._watchlist

        with Horizontal(id="bot-row"):
            yield self._tape
            yield self._pnl

        yield self._arb_alert
        yield self._status
        yield self._command

    def on_mount(self) -> None:
        self._cache.add_listener(self._on_cache_update)
        self._status.is_paper = not self._settings.live_mode
        self.set_interval(1.0, self._periodic_refresh)

    def _on_cache_update(self) -> None:
        self.call_from_thread(self._refresh_ui)

    def _periodic_refresh(self) -> None:
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        state = self._cache.active_state
        if not state:
            return

        market = state.market
        self._header.set_market(
            market.question[:30],
            market.yes_price,
            market.no_price,
        )

        if state.orderbook:
            self._orderbook.update_book(state.orderbook)

        if state.candles:
            self._chart.update_candles(state.candles)

        self._watchlist.update_watchlist()
        self._pnl.update_pnl(self._cache.pnl_history)
        self._positions.update_positions(self._cache.positions)
        self._status.is_connected = self._cache.connected

    def on_command_input_command_submitted(self, event: CommandInput.CommandSubmitted) -> None:
        cmd = event.command.lower()
        if cmd.startswith("/search") or cmd == "/":
            self.app.action_search()
        elif cmd.startswith("/buy"):
            self._tape.add_message("Manual BUY not yet implemented", "#FFB000")
        elif cmd.startswith("/sell"):
            self._tape.add_message("Manual SELL not yet implemented", "#FFB000")
        elif cmd == "/positions":
            self._tape.add_message(f"Open positions: {len(self._cache.positions)}")
        elif cmd == "/help":
            self._tape.add_message("/search /buy /sell /positions /help")
        else:
            self._tape.add_message(f"Unknown command: {cmd}", "#FF073A")
