"""Status bar widget - connection, mode, clock, keybindings."""

from __future__ import annotations

from textual.reactive import reactive
from textual.widgets import Static


class StatusBar(Static):
    """Bottom status bar showing connection, mode, and controls."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #1A1A2E;
        color: #FFB000;
        padding: 0 1;
    }
    """

    is_paper: reactive[bool] = reactive(True, init=False)
    is_connected: reactive[bool] = reactive(False, init=False)
    signals_on: reactive[bool] = reactive(True, init=False)
    auto_trade: reactive[bool] = reactive(False, init=False)

    def on_mount(self) -> None:
        self.update(self._render_text())

    def _render_text(self) -> str:
        mode = "PAPER" if self.is_paper else "LIVE"
        conn = "Connected" if self.is_connected else "Disconnected"
        signals = "ON" if self.signals_on else "OFF"
        trade = "ON" if self.auto_trade else "OFF"
        return f" ({mode}) {conn} | Signals: {signals} | Auto-Trade: {trade} | q:quit | /:search | t:trade | s:settings"

    def _refresh_display(self) -> None:
        self.update(self._render_text())

    def watch_is_paper(self) -> None:
        self._refresh_display()

    def watch_is_connected(self) -> None:
        self._refresh_display()

    def watch_signals_on(self) -> None:
        self._refresh_display()

    def watch_auto_trade(self) -> None:
        self._refresh_display()
