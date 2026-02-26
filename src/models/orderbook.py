"""OrderBook and OrderLevel frozen dataclasses with derived properties."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderLevel:
    """A single price level in the order book."""

    price: float
    size: float


@dataclass(frozen=True)
class OrderBook:
    """Full order book with bid and ask sides."""

    token_id: str
    bids: tuple[OrderLevel, ...] = field(default_factory=tuple)
    asks: tuple[OrderLevel, ...] = field(default_factory=tuple)
    timestamp: float = 0.0

    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 1.0

    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid

    @property
    def midpoint(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def imbalance(self) -> float:
        """Order book imbalance: positive = more bids (bullish)."""
        bid_depth = sum(level.size for level in self.bids[:5])
        ask_depth = sum(level.size for level in self.asks[:5])
        total = bid_depth + ask_depth
        if total == 0:
            return 0.0
        return (bid_depth - ask_depth) / total

    @property
    def bid_depth(self) -> float:
        return sum(level.size for level in self.bids)

    @property
    def ask_depth(self) -> float:
        return sum(level.size for level in self.asks)
