"""Arbitrage detection: YES + NO < $1.00 opportunities."""

from __future__ import annotations

from dataclasses import dataclass

from src.data.market_cache import MarketCache


@dataclass(frozen=True)
class ArbOpportunity:
    """A detected arbitrage opportunity."""

    market_id: str
    market_name: str
    yes_price: float
    no_price: float
    total_cost: float
    profit_per_share: float

    @property
    def return_pct(self) -> float:
        if self.total_cost == 0:
            return 0.0
        return (self.profit_per_share / self.total_cost) * 100.0


class ArbitrageDetector:
    """Scans markets for YES + NO < threshold arbitrage."""

    def __init__(self, threshold: float = 0.99) -> None:
        self._threshold = threshold

    def scan(self, cache: MarketCache) -> list[ArbOpportunity]:
        """Scan all cached markets for arbitrage opportunities."""
        opportunities: list[ArbOpportunity] = []

        for state in cache.all_states():
            market = state.market
            yes_price = market.yes_price
            no_price = market.no_price

            if yes_price <= 0 or no_price <= 0:
                continue

            total = yes_price + no_price
            if total < self._threshold:
                profit = 1.0 - total
                opportunities.append(
                    ArbOpportunity(
                        market_id=market.condition_id,
                        market_name=market.question,
                        yes_price=yes_price,
                        no_price=no_price,
                        total_cost=total,
                        profit_per_share=profit,
                    )
                )

        return sorted(opportunities, key=lambda o: o.profit_per_share, reverse=True)
