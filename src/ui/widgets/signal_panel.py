"""Signal indicator panel showing all 7 signals + composite gauge."""

from __future__ import annotations

from textual.widgets import Static

from src.models.signal import CompositeScore, SignalDirection


class SignalPanel(Static):
    """Display panel for all trading signals and composite score."""

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
        super().__init__("Waiting for data...", **kwargs)
        self._score: CompositeScore | None = None

    def update_score(self, score: CompositeScore) -> None:
        self._score = score
        self._redraw()

    def _redraw(self) -> None:
        if not self._score:
            return

        score = self._score
        direction = score.direction
        arrow = self._direction_arrow(direction)
        pct = score.strength_pct

        lines = [
            f"SIGNALS",
            f"COMPOSITE: {arrow} {direction.value} {score.score:+.2f} ({pct:.0f}%)",
        ]

        if score.boundary_suppressed:
            lines.append("  (boundary suppressed)")

        signal_parts: list[str] = []
        for sig in score.signals:
            signal_parts.append(f"{sig.name} {sig.value:+.2f}")

        for i in range(0, len(signal_parts), 3):
            chunk = signal_parts[i : i + 3]
            lines.append("  " + "  ".join(chunk))

        gauge = self._render_gauge(score.score)
        lines.append(f"\n  {gauge}")

        self.update("\n".join(lines))

    def _direction_arrow(self, direction: SignalDirection) -> str:
        if direction == SignalDirection.BUY:
            return ">>>"
        elif direction == SignalDirection.SELL:
            return "<<<"
        return "---"

    def _render_gauge(self, score: float) -> str:
        width = 30
        center = width // 2
        pos = int((score + 1) / 2 * width)
        pos = max(0, min(width - 1, pos))

        bar = list("-" * width)
        bar[center] = "|"
        bar[pos] = "#"
        bar_str = "".join(bar)
        return f"SELL {bar_str} BUY"
