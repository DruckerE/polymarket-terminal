"""Arbitrage opportunity alert widget."""

from __future__ import annotations

from textual.widgets import Static


class ArbitrageAlert(Static):
    """Displays arbitrage alerts when YES+NO < threshold."""

    DEFAULT_CSS = """
    ArbitrageAlert {
        height: auto;
        max-height: 2;
        background: #000000;
        color: #00D4FF;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)

    def set_alert(self, market_name: str, yes_price: float, no_price: float) -> None:
        total = yes_price + no_price
        spread = 1.0 - total
        self.update(
            f"ARB: {market_name[:20]} YES+NO=${total:.3f} +${spread:.3f}/sh"
        )

    def clear_alerts(self) -> None:
        self.update("")
