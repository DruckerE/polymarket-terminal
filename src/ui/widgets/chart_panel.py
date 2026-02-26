"""Candlestick chart panel using textual-plotext."""

from __future__ import annotations

from textual.containers import Container
from textual.widgets import Static

from src.models.candle import Candle

try:
    from textual_plotext import PlotextPlot

    HAS_PLOTEXT = True
except ImportError:
    HAS_PLOTEXT = False


class ChartPanel(Container):
    """Candlestick chart rendered via textual-plotext."""

    DEFAULT_CSS = """
    ChartPanel {
        width: 3fr;
        height: 100%;
        border: solid #333333;
        background: #000000;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._candles: list[Candle] = []

    def compose(self):
        if HAS_PLOTEXT:
            yield PlotextPlot(id="price-chart")
        else:
            yield Static("Chart requires textual-plotext")

    def update_candles(self, candles: tuple[Candle, ...] | list[Candle]) -> None:
        self._candles = list(candles)
        self._redraw()

    def _redraw(self) -> None:
        if not HAS_PLOTEXT or not self._candles:
            return

        try:
            plot_widget = self.query_one("#price-chart", PlotextPlot)
        except Exception:
            return

        plt = plot_widget.plt
        plt.clear_figure()
        plt.theme("dark")
        plt.canvas_color("black")
        plt.axes_color("black")
        plt.ticks_color("gray")

        display_candles = self._candles[-50:]
        x_indices = list(range(len(display_candles)))
        opens = [c.open for c in display_candles]
        highs = [c.high for c in display_candles]
        lows = [c.low for c in display_candles]
        closes = [c.close for c in display_candles]

        plt.candlestick(
            x_indices,
            {"Open": opens, "Close": closes, "High": highs, "Low": lows},
        )
        plt.title("Price (5m candles)")
        plt.ylabel("Price")

        if len(display_candles) >= 2:
            total_tp_vol = 0.0
            total_vol = 0.0
            vwap_values = []
            for c in display_candles:
                total_tp_vol += c.typical_price * c.volume
                total_vol += c.volume
                vwap_values.append(total_tp_vol / total_vol if total_vol > 0 else c.close)
            plt.plot(x_indices, vwap_values, color="cyan", label="VWAP")

        plot_widget.refresh()
