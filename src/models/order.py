"""Order, OrderRequest, and OrderResponse frozen dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.models.position import OutcomeType, Side


class OrderStatus(Enum):
    """Order lifecycle status."""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderType(Enum):
    """Order type."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass(frozen=True)
class OrderRequest:
    """Request to place an order."""

    market_id: str
    token_id: str
    side: Side
    outcome: OutcomeType
    price: float
    size: float
    order_type: OrderType = OrderType.LIMIT


@dataclass(frozen=True)
class Order:
    """A tracked order."""

    order_id: str
    request: OrderRequest
    status: OrderStatus = OrderStatus.PENDING
    filled_size: float = 0.0
    filled_price: float = 0.0
    timestamp: float = 0.0
    error: str = ""


@dataclass(frozen=True)
class OrderResponse:
    """Response from order placement."""

    success: bool
    order_id: str = ""
    error: str = ""
