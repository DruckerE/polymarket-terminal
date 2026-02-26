"""Paper trade simulator for risk-free strategy testing."""

from __future__ import annotations

import time
import uuid

from src.models.order import Order, OrderRequest, OrderResponse, OrderStatus
from src.models.position import OutcomeType, Side, Trade


class PaperBroker:
    """Simulates order execution for paper trading."""

    def __init__(self, starting_balance: float = 1000.0) -> None:
        self._balance = starting_balance
        self._starting_balance = starting_balance
        self._orders: list[Order] = []
        self._trades: list[Trade] = []

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def starting_balance(self) -> float:
        return self._starting_balance

    @property
    def trades(self) -> tuple[Trade, ...]:
        return tuple(self._trades)

    @property
    def orders(self) -> tuple[Order, ...]:
        return tuple(self._orders)

    def place_order(self, request: OrderRequest) -> OrderResponse:
        """Simulate immediate fill at requested price."""
        cost = request.price * request.size

        if request.side == Side.BUY:
            if cost > self._balance:
                return OrderResponse(
                    success=False,
                    error=f"Insufficient balance: ${self._balance:.2f} < ${cost:.2f}",
                )
            self._balance -= cost
        else:
            self._balance += cost

        order_id = str(uuid.uuid4())[:8]
        now = time.time()

        order = Order(
            order_id=order_id,
            request=request,
            status=OrderStatus.FILLED,
            filled_size=request.size,
            filled_price=request.price,
            timestamp=now,
        )
        self._orders.append(order)

        trade = Trade(
            trade_id=order_id,
            market_id=request.market_id,
            token_id=request.token_id,
            side=request.side,
            outcome=request.outcome,
            price=request.price,
            size=request.size,
            timestamp=now,
            is_paper=True,
        )
        self._trades.append(trade)

        return OrderResponse(success=True, order_id=order_id)

    def reset(self) -> None:
        self._balance = self._starting_balance
        self._orders = []
        self._trades = []
