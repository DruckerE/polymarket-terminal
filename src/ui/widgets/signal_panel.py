"""Signal panel — scalper state display: watching, in-trade, results, summary."""

from __future__ import annotations

import time

from textual.widgets import Static

from src.data.market_scanner import ScanResult
from src.trading.scalper import Scalper


class SignalPanel(Static):
    """Display live scalper state: prices, OBI, position, P&L."""

    DEFAULT_CSS = """
    SignalPanel {
        width: 3fr;
        height: 100%;
        min-height: 6;
        border: solid #333333;
        background: #000000;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("Scanning for market...", **kwargs)
        self._scalper: Scalper | None = None
        self._scan: ScanResult | None = None
        self._balance: float = 100.0
        self._total_pnl: float = 0.0
        self._win_rate: float = 0.0
        self._wins: int = 0
        self._losses: int = 0

    def set_scalp_state(
        self,
        scalper: Scalper,
        scan: ScanResult | None = None,
        balance: float = 100.0,
        total_pnl: float = 0.0,
        win_rate: float = 0.0,
        wins: int = 0,
        losses: int = 0,
    ) -> None:
        """Update display with current scalper state."""
        self._scalper = scalper
        self._scan = scan
        self._balance = balance
        self._total_pnl = total_pnl
        self._win_rate = win_rate
        self._wins = wins
        self._losses = losses
        self._redraw()

    def _redraw(self) -> None:
        scalper = self._scalper
        scan = self._scan

        if scalper is None or scan is None:
            self.update("Scanning for market...")
            return

        pos = scalper.position
        if pos is not None:
            self._draw_in_trade(scalper, pos)
        else:
            self._draw_watching(scalper)

    def _draw_watching(self, scalper: Scalper) -> None:
        """WATCHING: show prices, OBI, flat status, and window summary."""
        yes_p = scalper.yes_price
        no_p = scalper.no_price
        yes_obi = scalper.yes_obi
        no_obi = scalper.no_obi

        # Determine dominant OBI for display
        obi = yes_obi if abs(yes_obi) >= abs(no_obi) else no_obi

        lines = []

        # Line 1: Prices
        if yes_p > 0 or no_p > 0:
            lines.append(f"YES ${yes_p:.3f} / NO ${no_p:.3f} | OBI {obi:+.2f} | Flat")
        else:
            lines.append("Waiting for prices...")

        # Line 2: Last result (if any this window)
        results = scalper.results
        if results:
            last = results[-1]
            pnl_str = f"+${last.pnl:.2f}" if last.pnl >= 0 else f"-${abs(last.pnl):.2f}"
            lines.append(f"  Last: {last.side} {pnl_str} ({last.exit_reason})")

        # Line 3: Window stats
        if results:
            w_pnl = sum(r.pnl for r in results)
            w_wins = sum(1 for r in results if r.pnl > 0)
            w_losses = len(results) - w_wins
            pnl_str = f"+${w_pnl:.2f}" if w_pnl >= 0 else f"-${abs(w_pnl):.2f}"
            lines.append(f"  Window: {len(results)} trades | {w_wins}W {w_losses}L | {pnl_str}")

        # Line 4: Session balance
        pnl_str = f"+${self._total_pnl:.2f}" if self._total_pnl >= 0 else f"-${abs(self._total_pnl):.2f}"
        total = self._wins + self._losses
        if total > 0:
            lines.append(
                f"  ${self._balance:.2f} ({pnl_str}) | "
                f"{self._wins}W {self._losses}L ({self._win_rate:.0f}%)"
            )
        else:
            lines.append(f"  ${self._balance:.2f} | No trades yet")

        # Line 5: Cooldown / max trades info
        trades_left = scalper.max_trades - scalper.trade_count
        if trades_left <= 0:
            lines.append("  Max trades reached — waiting for next window")
        else:
            cooldown = scalper.cooldown_remaining
            if cooldown > 0:
                lines.append(f"  Cooldown: {cooldown:.0f}s")

        self.update("\n".join(lines))

    def _draw_in_trade(self, scalper: Scalper, pos) -> None:
        """IN TRADE: show entry, target, unrealized P&L, hold time."""
        current_price = scalper.current_price_for_position()
        unrealized = (current_price - pos.entry_price) * pos.shares
        hold_secs = time.time() - pos.entry_time

        lines = []

        # Line 1: Position
        lines.append(
            f"LONG {pos.side} @ ${pos.entry_price:.3f} → "
            f"target ${pos.target_price:.3f}"
        )

        # Line 2: Current price + unrealized P&L
        pnl_str = f"+${unrealized:.2f}" if unrealized >= 0 else f"-${abs(unrealized):.2f}"
        lines.append(f"  Now ${current_price:.3f} | {pnl_str} | {hold_secs:.0f}s")

        # Line 3: Stop loss
        lines.append(f"  Stop ${pos.stop_price:.3f} | Max hold {scalper.max_hold:.0f}s")

        # Line 4: Session balance
        pnl_str = f"+${self._total_pnl:.2f}" if self._total_pnl >= 0 else f"-${abs(self._total_pnl):.2f}"
        lines.append(f"  ${self._balance:.2f} ({pnl_str})")

        # Line 5: Trade count this window
        lines.append(f"  Trade #{scalper.trade_count}/{scalper.max_trades} this window")

        self.update("\n".join(lines))
