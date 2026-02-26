"""Order execution router - dispatches to paper or live broker."""

from __future__ import annotations

import logging

from src.models.order import OrderRequest, OrderResponse
from src.trading.paper_broker import PaperBroker

logger = logging.getLogger(__name__)


class Executor:
    """Routes orders to paper or live broker based on mode."""

    def __init__(self, live_mode: bool = False, paper_balance: float = 1000.0) -> None:
        self._live_mode = live_mode
        self._paper_broker = PaperBroker(starting_balance=paper_balance)

    @property
    def is_live(self) -> bool:
        return self._live_mode

    @property
    def balance(self) -> float:
        if self._live_mode:
            return 0.0
        return self._paper_broker.balance

    @property
    def paper_broker(self) -> PaperBroker:
        return self._paper_broker

    async def execute(self, request: OrderRequest) -> OrderResponse:
        """Execute an order through the appropriate broker."""
        if self._live_mode:
            return await self._execute_live(request)
        return self._execute_paper(request)

    def _execute_paper(self, request: OrderRequest) -> OrderResponse:
        logger.info(
            "Paper %s %s %s @ $%.3f x%.0f",
            request.side.value,
            request.outcome.value,
            request.market_id[:8],
            request.price,
            request.size,
        )
        return self._paper_broker.place_order(request)

    async def _execute_live(self, request: OrderRequest) -> OrderResponse:
        """Execute via Polymarket CLOB API.

        Live execution requires py-clob-client with L2 HMAC auth.
        This is a placeholder that returns an error until credentials
        are configured and the integration is validated.
        """
        logger.warning("Live execution not yet implemented")
        return OrderResponse(
            success=False,
            error="Live trading requires API credentials and explicit enablement",
        )
