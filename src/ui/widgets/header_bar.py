"""Header bar widget - market info, price, countdown timer."""

from __future__ import annotations

from textual.widgets import Static


class HeaderBar(Static):
    """Bloomberg-style header with title, market info, and countdown."""

    DEFAULT_CSS = """
    HeaderBar {
        dock: top;
        height: 3;
        background: #1A1A2E;
        color: #FFB000;
        text-style: bold;
        padding: 1 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._market_name = "NO MARKET SELECTED"
        self._yes_price = "--"
        self._no_price = "--"
        self._countdown = "--:--"

    def on_mount(self) -> None:
        self._redraw()

    def set_market(self, name: str, yes_price: float, no_price: float) -> None:
        self._market_name = name[:30]
        self._yes_price = f"{yes_price:.2f}"
        self._no_price = f"{no_price:.2f}"
        self._redraw()

    def set_countdown(self, seconds: float) -> None:
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        self._countdown = f"{minutes:02d}:{secs:02d}"
        self._redraw()

    def _redraw(self) -> None:
        text = (
            f"POLYMARKET TERMINAL  |  "
            f"{self._market_name}  ${self._yes_price} / ${self._no_price}  |  "
            f"{self._countdown} remaining"
        )
        self.update(text)
