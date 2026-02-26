"""Main Textual App - Bloomberg Terminal TUI for Polymarket."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from src.config.settings import AppSettings
from src.data.candle_aggregator import CandleAggregator
from src.data.market_cache import MarketCache
from src.data.websocket_feed import EventType, WebSocketFeed, WSEvent
from src.signals.composite import CompositeEngine
from src.trading.arbitrage import ArbitrageDetector
from src.trading.engine import TradingEngine
from src.trading.executor import Executor
from src.trading.position_tracker import PositionTracker
from src.ui.screens.main_screen import MainScreen
from src.ui.screens.market_search import MarketSearchScreen
from src.ui.screens.settings_screen import SettingsScreen

logger = logging.getLogger(__name__)

CSS_PATH = Path(__file__).parent / "styles.tcss"


class PolymarketTerminal(App):
    """Bloomberg Terminal-style TUI for Polymarket prediction markets."""

    TITLE = "POLYMARKET TERMINAL"
    CSS_PATH = CSS_PATH

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("slash", "search", "Search", key_display="/"),
        Binding("t", "toggle_auto_trade", "Auto-Trade"),
        Binding("s", "open_settings", "Settings"),
        Binding("p", "toggle_paper", "Paper/Live"),
        Binding("r", "refresh_data", "Refresh"),
    ]

    def __init__(self, settings: AppSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AppSettings.default()
        self.cache = MarketCache()
        self.auto_trade_enabled = False
        self.signals_enabled = True

        self._ws_feed = WebSocketFeed()
        self._aggregator = CandleAggregator(settings.trading.candle_interval if settings else 300)
        self._composite = CompositeEngine(self.settings.weights)
        self._executor = Executor(
            live_mode=self.settings.live_mode,
            paper_balance=self.settings.trading.paper_balance,
        )
        self._tracker = PositionTracker(self.settings.trading.paper_balance)
        self._engine = TradingEngine(
            cache=self.cache,
            executor=self._executor,
            tracker=self._tracker,
            composite=self._composite,
            settings=self.settings.trading,
        )
        self._arb_detector = ArbitrageDetector(self.settings.trading.arb_threshold)

    def compose(self) -> ComposeResult:
        yield MainScreen(self.cache, self.settings)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "POLYMARKET TERMINAL"
        self.sub_title = "PAPER MODE" if not self.settings.live_mode else "LIVE MODE"

        self._ws_feed.on_event(EventType.BOOK, self._on_book_event)
        self._ws_feed.on_event(EventType.TRADE, self._on_trade_event)
        self._ws_feed.on_event(EventType.PRICE, self._on_price_event)
        self._ws_feed.set_connect_handler(lambda: setattr(self.cache, "connected", True))
        self._ws_feed.set_disconnect_handler(lambda: setattr(self.cache, "connected", False))

        self.set_interval(self.settings.trading.signal_recalc_interval, self._signal_tick)
        self.set_interval(10.0, self._arb_scan)

    def action_search(self) -> None:
        def on_market_selected(market) -> None:
            if market and hasattr(market, "condition_id"):
                self._on_market_chosen(market)

        self.push_screen(MarketSearchScreen(self.cache), on_market_selected)

    def action_toggle_auto_trade(self) -> None:
        self.auto_trade_enabled = not self.auto_trade_enabled
        self._engine.enabled = self.auto_trade_enabled
        status = "ON" if self.auto_trade_enabled else "OFF"
        self.notify(f"Auto-Trade: {status}", severity="information")

    def action_open_settings(self) -> None:
        self.push_screen(SettingsScreen(self.settings))

    def action_toggle_paper(self) -> None:
        if self.settings.live_mode:
            self.notify("Cannot switch to paper from live mode at runtime", severity="warning")
            return
        self.notify("Paper mode active", severity="information")

    def action_refresh_data(self) -> None:
        self.notify("Refreshing data...", severity="information")

    def _on_market_chosen(self, market) -> None:
        yes = market.yes_outcome
        if yes:
            self.run_worker(self._ws_feed.subscribe(yes.token_id))

        no = market.no_outcome
        if no:
            self.run_worker(self._ws_feed.subscribe(no.token_id))

        if not self._ws_feed.is_connected:
            self.run_worker(self._ws_feed.start())

    def _on_book_event(self, event: WSEvent) -> None:
        from src.models.orderbook import OrderBook, OrderLevel

        bids_raw = event.data.get("bids", [])
        asks_raw = event.data.get("asks", [])

        bids = tuple(
            OrderLevel(price=float(b.get("price", 0)), size=float(b.get("size", 0)))
            for b in bids_raw
        )
        asks = tuple(
            OrderLevel(price=float(a.get("price", 0)), size=float(a.get("size", 0)))
            for a in asks_raw
        )

        book = OrderBook(
            token_id=event.asset_id,
            bids=tuple(sorted(bids, key=lambda x: x.price, reverse=True)),
            asks=tuple(sorted(asks, key=lambda x: x.price)),
            timestamp=event.timestamp,
        )

        active = self.cache.active_state
        if active and active.market.condition_id:
            self.cache.update_orderbook(active.market.condition_id, book)

    def _on_trade_event(self, event: WSEvent) -> None:
        price = float(event.data.get("price", 0))
        if price <= 0:
            return

        active = self.cache.active_state
        if active:
            self.cache.update_price(active.market.condition_id, price)
            candle = self._aggregator.add_tick(price, size=1.0)
            if candle:
                self.cache.add_candle(active.market.condition_id, candle)

    def _on_price_event(self, event: WSEvent) -> None:
        price = float(event.data.get("price", 0))
        if price <= 0:
            return

        active = self.cache.active_state
        if active:
            self.cache.update_price(active.market.condition_id, price)

    async def _signal_tick(self) -> None:
        if not self.signals_enabled:
            return

        state = self.cache.active_state
        if state:
            score = self._composite.calculate(state)
            self.cache.update_score(state.market.condition_id, score)

        if self.auto_trade_enabled:
            await self._engine.tick()

    def _arb_scan(self) -> None:
        opportunities = self._arb_detector.scan(self.cache)
        if opportunities:
            opp = opportunities[0]
            try:
                main_screen = self.query_one(MainScreen)
                main_screen._arb_alert.set_alert(opp.market_name, opp.yes_price, opp.no_price)
                main_screen._tape.add_arb_alert(opp.yes_price, opp.no_price)
            except Exception:
                pass
