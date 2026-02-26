"""Main Textual App — scalp-mode Bloomberg Terminal TUI for Polymarket."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from src.config.constants import SCALP_BET_SIZE
from src.config.settings import AppSettings
from src.data.clob_client import get_midpoint, get_orderbook
from src.data.market_cache import MarketCache
from src.data.market_scanner import MarketScanner, ScanResult
from src.data.websocket_feed import EventType, WebSocketFeed, WSEvent
from src.models.orderbook import OrderBook, OrderLevel
from src.storage.scalp_csv_logger import ScalpCsvLogger
from src.trading.scalper import Scalper, ScalpResult
from src.ui.screens.main_screen import MainScreen
from src.ui.screens.market_search import MarketSearchScreen
from src.ui.screens.settings_screen import SettingsScreen

logger = logging.getLogger(__name__)

CSS_PATH = Path(__file__).parent / "styles.tcss"


class PolymarketTerminal(App):
    """Bloomberg Terminal-style TUI for Polymarket — scalp mode."""

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

        self._ws_feed = WebSocketFeed()
        self._scalper = Scalper(bet_size=SCALP_BET_SIZE)
        self._csv_logger = ScalpCsvLogger()

        self._scanner = MarketScanner(poll_interval=15.0)
        self._scanner.on_market_found(self._on_scanner_found)
        self._scanner.on_market_expired(self._on_scanner_expired)
        self._current_scan: ScanResult | None = None

        # Scalp session state
        self._starting_balance: float = 100.0
        self._balance: float = 100.0
        self._total_trades: int = 0
        self._total_wins: int = 0
        self._total_losses: int = 0

        # Track token IDs for current market
        self._yes_token_id: str = ""
        self._no_token_id: str = ""

    def compose(self) -> ComposeResult:
        yield MainScreen(self.cache, self.settings)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "POLYMARKET TERMINAL"
        self.sub_title = "SCALP MODE"

        self._ws_feed.on_event(EventType.BOOK, self._on_book_event)
        self._ws_feed.on_event(EventType.TRADE, self._on_trade_event)
        self._ws_feed.on_event(EventType.PRICE, self._on_price_event)
        self._ws_feed.set_connect_handler(lambda: setattr(self.cache, "connected", True))
        self._ws_feed.set_disconnect_handler(lambda: setattr(self.cache, "connected", False))

        self.set_interval(1.0, self._update_countdown)
        self.set_interval(5.0, self._poll_data)

        self.run_worker(self._scanner.start(), exclusive=True, group="scanner")

    # ── Actions ───────────────────────────────────────────────────────

    def action_search(self) -> None:
        def on_market_selected(market) -> None:
            if market and hasattr(market, "condition_id"):
                self._on_market_chosen(market)

        self.push_screen(MarketSearchScreen(self.cache), on_market_selected)

    def action_toggle_auto_trade(self) -> None:
        self.auto_trade_enabled = not self.auto_trade_enabled
        status = "ON" if self.auto_trade_enabled else "OFF"
        self.notify(f"Auto-Trade: {status}", severity="information")

    def action_open_settings(self) -> None:
        self.push_screen(SettingsScreen(self.settings))

    def action_toggle_paper(self) -> None:
        self.notify("Paper mode active", severity="information")

    def action_refresh_data(self) -> None:
        self.notify("Refreshing data...", severity="information")

    # ── Market setup ──────────────────────────────────────────────────

    def _on_market_chosen(self, market) -> None:
        """Subscribe to BOTH yes AND no tokens via WebSocket."""
        yes = market.yes_outcome
        if yes and yes.token_id:
            self._yes_token_id = yes.token_id
            self.run_worker(self._ws_feed.subscribe(yes.token_id))
        no = market.no_outcome
        if no and no.token_id:
            self._no_token_id = no.token_id
            self.run_worker(self._ws_feed.subscribe(no.token_id))
        if not self._ws_feed.is_connected:
            self.run_worker(self._ws_feed.start())

        self._scalper.set_tokens(self._yes_token_id, self._no_token_id)

    def _on_scanner_found(self, result: ScanResult) -> None:
        """Scanner found a new market — force exit any open position, reset scalper."""
        self._force_exit_and_log(result)

        self._current_scan = result
        self._scalper.reset()

        market = result.market
        if not market:
            return
        logger.info("Scanner found market: %s (%s)", result.slug, result.status)
        self.cache.set_market(market)
        self.cache.active_market_id = market.condition_id
        self._on_market_chosen(market)
        self._tape_msg(f"New market: {result.slug}")

    def _on_scanner_expired(self, result: ScanResult) -> None:
        """Scanner: market expired — force exit, log window summary."""
        logger.info("Scanner: market expired %s", result.slug)
        self._force_exit_and_log(result)
        self._log_window_summary(result)
        self._current_scan = None

    # ── WebSocket event handlers ──────────────────────────────────────

    def _on_book_event(self, event: WSEvent) -> None:
        """Feed orderbook update to scalper + cache."""
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

        # Feed to scalper for OBI detection
        self._scalper.on_book_update(event.asset_id, book)

        # Also update cache for UI
        active = self.cache.active_state
        if active and active.market.condition_id:
            self.cache.update_orderbook(active.market.condition_id, book)

    def _on_trade_event(self, event: WSEvent) -> None:
        """Feed trade tick to scalper for volume tracking + price updates."""
        price = float(event.data.get("price", 0))
        size = float(event.data.get("size", 1))
        if price <= 0:
            return

        scan = self._current_scan
        if not scan:
            return

        # Volume tracking (no price — on_price_tick handles that)
        self._scalper.on_trade_tick(event.asset_id, size)

        # Price tick for entry/exit detection
        action = self._scalper.on_price_tick(event.asset_id, price, scan.window_end)
        self._handle_scalp_action(action)

        # Update cache
        active = self.cache.active_state
        if active:
            self.cache.update_price(active.market.condition_id, price)

        self._update_signal_display()

    def _on_price_event(self, event: WSEvent) -> None:
        """Feed price change to scalper."""
        price = float(event.data.get("price", 0))
        if price <= 0:
            return

        scan = self._current_scan
        if not scan:
            return

        action = self._scalper.on_price_tick(event.asset_id, price, scan.window_end)
        self._handle_scalp_action(action)

        active = self.cache.active_state
        if active:
            self.cache.update_price(active.market.condition_id, price)

        self._update_signal_display()

    # ── REST polling ──────────────────────────────────────────────────

    async def _poll_data(self) -> None:
        """Every 5s: fetch REST data, feed to scalper, update display."""
        self._update_signal_display()

        scan = self._current_scan
        if not scan or not scan.market:
            return

        market = scan.market

        # First time seeing this market — set up subscriptions
        if self.cache.active_market_id != market.condition_id:
            self.cache.set_market(market)
            self.cache.active_market_id = market.condition_id
            self._on_market_chosen(market)
            self._tape_msg(f"New market: {scan.slug}")

        # Fetch orderbooks for both tokens and feed to scalper
        await self._fetch_and_feed(scan)

        self._update_signal_display()

    async def _fetch_and_feed(self, scan: ScanResult) -> None:
        """Fetch REST data for both tokens and feed prices to scalper."""
        market = scan.market
        if not market:
            return

        window_end = scan.window_end

        # Fetch YES token
        yes = market.yes_outcome
        if yes and yes.token_id:
            try:
                book = await get_orderbook(yes.token_id)
                self._scalper.on_book_update(yes.token_id, book)
                self.cache.update_orderbook(market.condition_id, book)
            except Exception as exc:
                logger.warning("Failed to fetch YES orderbook: %s", exc)

            try:
                price = await get_midpoint(yes.token_id)
                if price > 0:
                    action = self._scalper.on_price_tick(yes.token_id, price, window_end)
                    self._handle_scalp_action(action)
                    self.cache.update_price(market.condition_id, price)
            except Exception as exc:
                logger.warning("Failed to fetch YES midpoint: %s", exc)

        # Fetch NO token
        no = market.no_outcome
        if no and no.token_id:
            try:
                no_book = await get_orderbook(no.token_id)
                self._scalper.on_book_update(no.token_id, no_book)
            except Exception as exc:
                logger.warning("Failed to fetch NO orderbook: %s", exc)

            try:
                no_price = await get_midpoint(no.token_id)
                if no_price > 0:
                    action = self._scalper.on_price_tick(no.token_id, no_price, window_end)
                    self._handle_scalp_action(action)
            except Exception as exc:
                logger.warning("Failed to fetch NO midpoint: %s", exc)

    # ── Scalp action handling ─────────────────────────────────────────

    def _handle_scalp_action(self, action: str) -> None:
        """Process scalper action: BUY_YES, BUY_NO, SELL, or HOLD."""
        if action == "HOLD":
            return

        scan = self._current_scan

        if action in ("BUY_YES", "BUY_NO"):
            pos = self._scalper.position
            if pos:
                self._tape_msg(
                    f"LONG {pos.side} @ ${pos.entry_price:.3f} → "
                    f"target ${pos.target_price:.3f} | "
                    f"{pos.shares:.1f} shares"
                )

        elif action == "SELL":
            results = self._scalper.results
            if results:
                result = results[-1]
                self._record_result(result, scan)

    def _record_result(self, result: ScalpResult, scan: ScanResult | None) -> None:
        """Record a completed scalp trade."""
        self._balance += result.pnl
        self._total_trades += 1
        if result.pnl > 0:
            self._total_wins += 1
        elif result.pnl < 0:
            self._total_losses += 1

        slug = scan.slug if scan else "unknown"
        self._csv_logger.log(result, slug, self._balance, self._total_trades)

        pnl_str = f"+${result.pnl:.2f}" if result.pnl >= 0 else f"-${abs(result.pnl):.2f}"
        self._tape_msg(
            f"SOLD {result.side} {pnl_str} ({result.exit_reason}) | "
            f"{result.hold_time:.0f}s | Balance ${self._balance:.2f}"
        )

    def _force_exit_and_log(self, scan: ScanResult | None) -> None:
        """Force exit any open position and record it."""
        result = self._scalper.force_exit("window_end")
        if result:
            self._record_result(result, scan)

    def _log_window_summary(self, scan: ScanResult) -> None:
        """Log a summary of the completed window."""
        results = self._scalper.results
        if not results:
            return

        window_pnl = sum(r.pnl for r in results)
        wins = sum(1 for r in results if r.pnl > 0)
        losses = len(results) - wins
        pnl_str = f"+${window_pnl:.2f}" if window_pnl >= 0 else f"-${abs(window_pnl):.2f}"

        self._tape_msg(
            f"WINDOW END: {len(results)} trades | {wins}W {losses}L | "
            f"{pnl_str} | Balance ${self._balance:.2f}"
        )

    # ── Signal panel display ──────────────────────────────────────────

    def _update_signal_display(self) -> None:
        """Push scalper state to the signal panel."""
        try:
            main_screen = self.query_one(MainScreen)
        except Exception:
            return

        total_pnl = self._balance - self._starting_balance
        total = self._total_wins + self._total_losses
        win_rate = (self._total_wins / total * 100) if total > 0 else 0.0

        main_screen._signals.set_scalp_state(
            scalper=self._scalper,
            scan=self._current_scan,
            balance=self._balance,
            total_pnl=total_pnl,
            win_rate=win_rate,
            wins=self._total_wins,
            losses=self._total_losses,
        )

    # ── Helpers ───────────────────────────────────────────────────────

    def _tape_msg(self, message: str) -> None:
        try:
            main_screen = self.query_one(MainScreen)
            main_screen._tape.add_message(message)
        except Exception:
            pass

    def _update_countdown(self) -> None:
        scan = self._current_scan
        if not scan:
            return
        try:
            main_screen = self.query_one(MainScreen)
            main_screen._header.set_countdown(scan.time_until_end)
        except Exception:
            pass
