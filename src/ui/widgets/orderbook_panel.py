"""Order book depth panel with bid/ask bars."""

from __future__ import annotations

from textual.widgets import Static

from src.models.orderbook import OrderBook

MAX_DISPLAY_LEVELS = 8
BAR_WIDTH = 12


class OrderBookPanel(Static):
    """Depth-of-book display with visual bid/ask bars."""

    DEFAULT_CSS = """
    OrderBookPanel {
        width: 1fr;
        min-width: 28;
        height: 100%;
        border: solid #333333;
        background: #000000;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("ORDERBOOK\nWaiting for data...", **kwargs)
        self._orderbook: OrderBook | None = None

    def update_book(self, orderbook: OrderBook) -> None:
        self._orderbook = orderbook
        self._redraw()

    def _redraw(self) -> None:
        if not self._orderbook:
            return

        book = self._orderbook
        asks = list(book.asks[:MAX_DISPLAY_LEVELS])
        bids = list(book.bids[:MAX_DISPLAY_LEVELS])

        max_size = 1.0
        for level in asks + bids:
            max_size = max(max_size, level.size)

        lines: list[str] = ["ORDERBOOK"]

        for level in reversed(asks):
            bar_len = int((level.size / max_size) * BAR_WIDTH)
            bar = "#" * bar_len
            lines.append(f"  {level.price:.3f}  {bar:<{BAR_WIDTH}}  {level.size:>8.1f}")

        spread = book.spread
        mid = book.midpoint
        lines.append(f"  --- {mid:.3f} SPREAD {spread:.3f} ---")

        for level in bids:
            bar_len = int((level.size / max_size) * BAR_WIDTH)
            bar = "#" * bar_len
            lines.append(f"  {level.price:.3f}  {bar:<{BAR_WIDTH}}  {level.size:>8.1f}")

        self.update("\n".join(lines))
