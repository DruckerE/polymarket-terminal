"""Trading engine: signal → order decision logic."""

from __future__ import annotations

import logging
import time

from src.config.settings import TradingSettings
from src.data.market_cache import MarketCache, MarketState
from src.models.order import OrderRequest, OrderType
from src.models.position import OutcomeType, Side
from src.models.signal import CompositeScore, SignalDirection
from src.signals.composite import CompositeEngine
from src.trading.executor import Executor
from src.trading.position_tracker import PositionTracker
from src.trading.risk import calculate_position_size, check_drawdown_circuit_breaker

logger = logging.getLogger(__name__)


class TradingEngine:
    """Core engine converting signals into order decisions."""

    def __init__(
        self,
        cache: MarketCache,
        executor: Executor,
        tracker: PositionTracker,
        composite: CompositeEngine,
        settings: TradingSettings,
    ) -> None:
        self._cache = cache
        self._executor = executor
        self._tracker = tracker
        self._composite = composite
        self._settings = settings
        self._enabled = False
        self._last_signal_time: dict[str, float] = {}
        self._circuit_breaker_active = False
        self._peak_equity = settings.paper_balance

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def circuit_breaker_active(self) -> bool:
        return self._circuit_breaker_active

    async def tick(self) -> None:
        """Run one trading cycle for the active market."""
        if not self._enabled:
            return

        state = self._cache.active_state
        if not state:
            return

        if self._circuit_breaker_active:
            return

        current_equity = self._executor.balance
        self._peak_equity = max(self._peak_equity, current_equity)

        if check_drawdown_circuit_breaker(
            current_equity, self._peak_equity, self._settings.max_drawdown_pct
        ):
            self._circuit_breaker_active = True
            logger.warning("Circuit breaker triggered at equity $%.2f", current_equity)
            return

        market_id = state.market.condition_id
        now = time.time()
        last = self._last_signal_time.get(market_id, 0)
        if now - last < self._settings.signal_recalc_interval:
            return

        score = self._composite.calculate(state)
        self._cache.update_score(market_id, score)
        self._last_signal_time[market_id] = now

        await self._maybe_trade(state, score)

    async def _maybe_trade(self, state: MarketState, score: CompositeScore) -> None:
        if score.direction == SignalDirection.HOLD:
            return

        market = state.market
        yes_outcome = market.yes_outcome
        if not yes_outcome:
            return

        price = state.last_price or market.yes_price
        if price <= 0 or price >= 1:
            return

        sizing = calculate_position_size(
            score=score.score,
            price=price,
            equity=self._executor.balance,
            settings=self._settings,
            open_positions=self._tracker.open_count,
        )

        if sizing.size <= 0:
            return

        if score.direction == SignalDirection.BUY:
            request = OrderRequest(
                market_id=market.condition_id,
                token_id=yes_outcome.token_id,
                side=Side.BUY,
                outcome=OutcomeType.YES,
                price=price,
                size=sizing.size,
                order_type=OrderType.LIMIT,
            )
        else:
            position_key = f"{market.condition_id}:{OutcomeType.YES.value}"
            if position_key not in self._tracker.positions:
                return
            pos = self._tracker.positions[position_key]
            request = OrderRequest(
                market_id=market.condition_id,
                token_id=yes_outcome.token_id,
                side=Side.SELL,
                outcome=OutcomeType.YES,
                price=price,
                size=min(sizing.size, pos.size),
                order_type=OrderType.LIMIT,
            )

        response = await self._executor.execute(request)
        if response.success:
            trade = self._executor.paper_broker.trades[-1]
            self._tracker.process_trade(trade)
            self._cache.add_trade(trade)

            snapshot = self._tracker.snapshot(self._executor.balance)
            self._cache.add_pnl_snapshot(snapshot)

            for mk, pos in self._tracker.positions.items():
                self._cache.set_position(pos.market_id, pos)

            logger.info(
                "Executed %s %s @ $%.3f x%.0f",
                request.side.value,
                request.outcome.value,
                request.price,
                request.size,
            )
