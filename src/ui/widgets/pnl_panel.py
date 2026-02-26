"""P&L panel with equity curve sparkline and statistics."""

from __future__ import annotations

from textual.widgets import Static

from src.models.position import PnLSnapshot

SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


class PnLPanel(Static):
    """P&L display with sparkline equity curve and trading statistics."""

    DEFAULT_CSS = """
    PnLPanel {
        width: 1fr;
        min-width: 28;
        height: 100%;
        border: solid #333333;
        background: #000000;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("P&L\nNo trades yet", **kwargs)
        self._snapshots: list[PnLSnapshot] = []

    def update_pnl(self, snapshots: list[PnLSnapshot] | tuple[PnLSnapshot, ...]) -> None:
        self._snapshots = list(snapshots)
        self._redraw()

    def _redraw(self) -> None:
        if not self._snapshots:
            self.update("P&L\nNo trades yet")
            return

        latest = self._snapshots[-1]
        pnl = latest.total_pnl
        sign = "+" if pnl >= 0 else ""
        sparkline = self._render_sparkline()

        lines = [
            "P&L",
            f"  {sparkline}  {sign}${pnl:.2f}",
            f"  WR: {latest.win_rate:.0f}%  Sharpe: {latest.sharpe_ratio:.2f}",
            f"  Max DD: -${abs(latest.max_drawdown):.2f}",
            f"  Trades: {latest.total_trades}  Equity: ${latest.total_equity:.2f}",
        ]
        self.update("\n".join(lines))

    def _render_sparkline(self) -> str:
        if not self._snapshots:
            return ""

        equities = [s.total_equity for s in self._snapshots[-20:]]
        if len(equities) < 2:
            return SPARKLINE_CHARS[-1]

        min_eq = min(equities)
        max_eq = max(equities)
        eq_range = max_eq - min_eq

        if eq_range == 0:
            return SPARKLINE_CHARS[4] * len(equities)

        chars = []
        for eq in equities:
            idx = int(((eq - min_eq) / eq_range) * (len(SPARKLINE_CHARS) - 1))
            chars.append(SPARKLINE_CHARS[idx])
        return "".join(chars)
