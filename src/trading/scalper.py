"""Scalp engine — buy momentum, ride $0.02, sell. Trade the token price, not the outcome."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from src.config.constants import (
    SCALP_BET_SIZE,
    SCALP_COOLDOWN_SECONDS,
    SCALP_EXIT_BEFORE_END,
    SCALP_MAX_HOLD_SECONDS,
    SCALP_MAX_TRADES_PER_WINDOW,
    SCALP_MOMENTUM_THRESHOLD,
    SCALP_OBI_THRESHOLD,
    SCALP_PRICE_HISTORY_LEN,
    SCALP_PROFIT_TARGET,
    SCALP_STOP_LOSS,
    SCALP_VOLUME_SPIKE_MULT,
)
from src.models.orderbook import OrderBook


@dataclass(frozen=True)
class ScalpPosition:
    """An open scalp position."""

    token_id: str
    side: str              # "YES" or "NO"
    entry_price: float
    shares: float
    entry_time: float
    target_price: float    # entry + profit_target
    stop_price: float      # entry - stop_loss


@dataclass(frozen=True)
class ScalpResult:
    """Completed scalp trade."""

    side: str
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    hold_time: float
    exit_reason: str       # "target", "stop", "time", "window_end"


class _TokenState:
    """Price + volume tracking for a single token."""

    __slots__ = ("prices", "trade_sizes", "book")

    def __init__(self, history_len: int) -> None:
        self.prices: deque[float] = deque(maxlen=history_len)
        self.trade_sizes: deque[float] = deque(maxlen=history_len)
        self.book: OrderBook | None = None


class Scalper:
    """Core scalp engine: detect momentum on YES/NO tokens, ride quick swings."""

    def __init__(
        self,
        bet_size: float = SCALP_BET_SIZE,
        profit_target: float = SCALP_PROFIT_TARGET,
        stop_loss: float = SCALP_STOP_LOSS,
        max_hold: float = SCALP_MAX_HOLD_SECONDS,
        cooldown: float = SCALP_COOLDOWN_SECONDS,
        max_trades: int = SCALP_MAX_TRADES_PER_WINDOW,
        exit_before_end: float = SCALP_EXIT_BEFORE_END,
        obi_threshold: float = SCALP_OBI_THRESHOLD,
        momentum_threshold: float = SCALP_MOMENTUM_THRESHOLD,
        volume_spike_mult: float = SCALP_VOLUME_SPIKE_MULT,
    ) -> None:
        self._bet_size = bet_size
        self._profit_target = profit_target
        self._stop_loss = stop_loss
        self._max_hold = max_hold
        self._cooldown = cooldown
        self._max_trades = max_trades
        self._exit_before_end = exit_before_end
        self._obi_threshold = obi_threshold
        self._momentum_threshold = momentum_threshold
        self._volume_spike_mult = volume_spike_mult

        self._position: ScalpPosition | None = None
        self._results: list[ScalpResult] = []
        self._trade_count: int = 0
        self._last_exit_time: float = 0.0

        history_len = SCALP_PRICE_HISTORY_LEN
        self._yes = _TokenState(history_len)
        self._no = _TokenState(history_len)

        self._yes_token_id: str = ""
        self._no_token_id: str = ""

    # ── Public API ────────────────────────────────────────────────────

    @property
    def position(self) -> ScalpPosition | None:
        return self._position

    @property
    def results(self) -> list[ScalpResult]:
        return list(self._results)

    @property
    def trade_count(self) -> int:
        return self._trade_count

    @property
    def window_pnl(self) -> float:
        return sum(r.pnl for r in self._results)

    @property
    def yes_price(self) -> float:
        return self._yes.prices[-1] if self._yes.prices else 0.0

    @property
    def no_price(self) -> float:
        return self._no.prices[-1] if self._no.prices else 0.0

    @property
    def yes_obi(self) -> float:
        return self._yes.book.imbalance if self._yes.book else 0.0

    @property
    def no_obi(self) -> float:
        return self._no.book.imbalance if self._no.book else 0.0

    @property
    def max_trades(self) -> int:
        return self._max_trades

    @property
    def max_hold(self) -> float:
        return self._max_hold

    @property
    def cooldown_remaining(self) -> float:
        if self._last_exit_time <= 0:
            return 0.0
        return max(0.0, self._cooldown - (time.time() - self._last_exit_time))

    def current_price_for_position(self) -> float:
        """Get current price for the held position's token."""
        if self._position is None:
            return 0.0
        state = self._state_for_token(self._position.token_id)
        return state.prices[-1] if state and state.prices else self._position.entry_price

    def set_tokens(self, yes_token_id: str, no_token_id: str) -> None:
        """Configure which token IDs map to YES and NO."""
        self._yes_token_id = yes_token_id
        self._no_token_id = no_token_id

    def reset(self) -> None:
        """Reset for a new window. Preserves config, clears state."""
        self._position = None
        self._results = []
        self._trade_count = 0
        self._last_exit_time = 0.0
        history_len = SCALP_PRICE_HISTORY_LEN
        self._yes = _TokenState(history_len)
        self._no = _TokenState(history_len)

    def on_book_update(self, token_id: str, book: OrderBook) -> None:
        """Feed an orderbook snapshot for a token."""
        state = self._state_for_token(token_id)
        if state is not None:
            state.book = book

    def on_trade_tick(self, token_id: str, size: float = 1.0) -> None:
        """Feed a trade tick for volume tracking only. Price comes via on_price_tick."""
        state = self._state_for_token(token_id)
        if state is None:
            return
        state.trade_sizes.append(size)

    def on_price_tick(self, token_id: str, price: float, window_end: float) -> str:
        """Called on every price update. Returns action: 'BUY_YES', 'BUY_NO', 'SELL', or 'HOLD'."""
        state = self._state_for_token(token_id)
        if state is None:
            return "HOLD"

        state.prices.append(price)
        now = time.time()

        # If holding — check exits
        if self._position is not None:
            return self._check_exit(now, window_end)

        # If flat — check entries
        return self._check_entry(now, window_end)

    def force_exit(self, reason: str = "window_end") -> ScalpResult | None:
        """Force exit any open position immediately."""
        if self._position is None:
            return None

        pos = self._position
        state = self._state_for_token(pos.token_id)
        current_price = state.prices[-1] if state and state.prices else pos.entry_price

        return self._close_position(current_price, reason)

    # ── Private: entry detection ──────────────────────────────────────

    def _check_entry(self, now: float, window_end: float) -> str:
        """Scan both tokens for entry signals."""
        if self._trade_count >= self._max_trades:
            return "HOLD"

        if now - self._last_exit_time < self._cooldown:
            return "HOLD"

        # Don't enter too close to window end
        if window_end - now < self._exit_before_end:
            return "HOLD"

        # Check YES token
        yes_signal = self._detect_signal(self._yes)
        if yes_signal:
            return self._open_position("YES", self._yes_token_id, self._yes, now)

        # Check NO token
        no_signal = self._detect_signal(self._no)
        if no_signal:
            return self._open_position("NO", self._no_token_id, self._no, now)

        return "HOLD"

    def _detect_signal(self, state: _TokenState) -> bool:
        """Return True if any entry signal fires for this token."""
        # Need minimum price history
        if len(state.prices) < 3:
            return False

        # Signal 1: OBI spike — only bullish (positive imbalance = bid-heavy)
        if state.book is not None and state.book.imbalance > self._obi_threshold:
            return True

        # Signal 2: Volume spike (trade size 2x average of PREVIOUS trades)
        if len(state.trade_sizes) >= 4:
            previous = list(state.trade_sizes)[:-1]
            recent_avg = sum(previous) / len(previous)
            if recent_avg > 0 and state.trade_sizes[-1] > recent_avg * self._volume_spike_mult:
                return True

        # Signal 3: Price momentum — moved $0.02+ UPWARD over last 3 ticks
        prices = list(state.prices)
        if len(prices) >= 3:
            move = prices[-1] - prices[-3]
            if move >= self._momentum_threshold:
                # Confirm consistent upward direction
                if prices[-1] > prices[-2] > prices[-3]:
                    return True

        return False

    def _open_position(self, side: str, token_id: str, state: _TokenState, now: float) -> str:
        """Open a new scalp position."""
        if not state.prices or not token_id:
            return "HOLD"

        entry_price = state.prices[-1]
        if entry_price <= 0:
            return "HOLD"

        shares = self._bet_size / entry_price

        self._position = ScalpPosition(
            token_id=token_id,
            side=side,
            entry_price=entry_price,
            shares=shares,
            entry_time=now,
            target_price=entry_price + self._profit_target,
            stop_price=entry_price - self._stop_loss,
        )
        self._trade_count += 1

        return f"BUY_{side}"

    # ── Private: exit detection ───────────────────────────────────────

    def _check_exit(self, now: float, window_end: float) -> str:
        """Check all exit conditions for current position."""
        pos = self._position
        if pos is None:
            return "HOLD"

        state = self._state_for_token(pos.token_id)
        if state is None or not state.prices:
            return "HOLD"

        current_price = state.prices[-1]

        # Exit 1: Profit target hit
        if current_price >= pos.target_price:
            self._close_position(current_price, "target")
            return "SELL"

        # Exit 2: Stop loss hit
        if current_price <= pos.stop_price:
            self._close_position(current_price, "stop")
            return "SELL"

        # Exit 3: Max hold time exceeded
        if now - pos.entry_time >= self._max_hold:
            self._close_position(current_price, "time")
            return "SELL"

        # Exit 4: Window about to end
        if window_end - now < self._exit_before_end:
            self._close_position(current_price, "window_end")
            return "SELL"

        return "HOLD"

    def _close_position(self, exit_price: float, reason: str) -> ScalpResult:
        """Close current position and record result."""
        pos = self._position
        if pos is None:
            raise ValueError("No position to close")

        now = time.time()
        pnl = (exit_price - pos.entry_price) * pos.shares
        hold_time = now - pos.entry_time

        result = ScalpResult(
            side=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            shares=pos.shares,
            pnl=pnl,
            hold_time=hold_time,
            exit_reason=reason,
        )

        self._results = [*self._results, result]
        self._position = None
        self._last_exit_time = now

        return result

    # ── Private: helpers ──────────────────────────────────────────────

    def _state_for_token(self, token_id: str) -> _TokenState | None:
        """Map a token_id to its tracking state."""
        if token_id == self._yes_token_id:
            return self._yes
        if token_id == self._no_token_id:
            return self._no
        return None
