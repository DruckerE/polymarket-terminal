"""Time & sales trade tape using RichLog."""

from __future__ import annotations

from datetime import datetime

from textual.containers import Container
from textual.widgets import RichLog

from src.models.position import Trade


class TradeTape(Container):
    """Real-time trade tape showing recent executions."""

    DEFAULT_CSS = """
    TradeTape {
        width: 3fr;
        height: 100%;
        border: solid #333333;
        background: #000000;
    }
    """

    def compose(self):
        yield RichLog(id="tape-log", highlight=True, markup=True, max_lines=100)

    def add_trade(self, trade: Trade) -> None:
        try:
            log = self.query_one("#tape-log", RichLog)
        except Exception:
            return

        ts = datetime.fromtimestamp(trade.timestamp).strftime("%H:%M:%S")
        side = trade.side.value

        log.write(
            f"{ts}  {side:<4}  "
            f"{trade.outcome.value}  "
            f"${trade.price:.2f} x{trade.size:.0f}  "
            f"${trade.notional:.2f}"
        )

    def add_message(self, message: str, style: str = "") -> None:
        try:
            log = self.query_one("#tape-log", RichLog)
        except Exception:
            return

        ts = datetime.now().strftime("%H:%M:%S")
        log.write(f"{ts}  {message}")

    def add_arb_alert(self, yes_price: float, no_price: float) -> None:
        total = yes_price + no_price
        spread = 1.0 - total
        self.add_message(f"ARB ALERT: YES+NO=${total:.2f}, +${spread:.3f}/sh")
