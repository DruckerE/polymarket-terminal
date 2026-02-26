"""Gamma API client for market search and discovery."""

from __future__ import annotations

import httpx

from src.config.constants import GAMMA_BASE_URL
from src.models.market import Market, Outcome


async def search_markets(query: str, limit: int = 20) -> list[Market]:
    """Search for markets by keyword."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GAMMA_BASE_URL}/markets",
            params={
                "closed": "false",
                "limit": limit,
                "order": "volume24hr",
                "ascending": "false",
                "tag": query if not query.strip() else None,
                "slug": None,
            },
        )
        resp.raise_for_status()
        return [_parse_market(m) for m in resp.json()]


async def search_markets_by_query(query: str, limit: int = 20) -> list[Market]:
    """Full-text search for markets."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GAMMA_BASE_URL}/markets",
            params={
                "closed": "false",
                "limit": limit,
                "order": "volume24hr",
                "ascending": "false",
            },
        )
        resp.raise_for_status()
        markets = resp.json()

        query_lower = query.lower()
        filtered = [m for m in markets if query_lower in m.get("question", "").lower()]
        return [_parse_market(m) for m in filtered[:limit]]


async def get_market(condition_id: str) -> Market | None:
    """Get a single market by condition ID."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{GAMMA_BASE_URL}/markets/{condition_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _parse_market(resp.json())


async def get_active_markets(limit: int = 50) -> list[Market]:
    """Get active markets sorted by volume."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GAMMA_BASE_URL}/markets",
            params={
                "closed": "false",
                "active": "true",
                "limit": limit,
                "order": "volume24hr",
                "ascending": "false",
            },
        )
        resp.raise_for_status()
        return [_parse_market(m) for m in resp.json()]


def _parse_market(data: dict) -> Market:
    """Parse raw API response into Market dataclass."""
    outcomes_raw = data.get("outcomes", [])
    tokens = data.get("clobTokenIds", [])
    prices = data.get("outcomePrices", [])

    parsed_outcomes: list[Outcome] = []
    for i, label in enumerate(outcomes_raw):
        token_id = tokens[i] if i < len(tokens) else ""
        price_str = prices[i] if i < len(prices) else "0"
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0
        parsed_outcomes.append(Outcome(token_id=token_id, label=label, price=price))

    return Market(
        condition_id=data.get("conditionId", data.get("id", "")),
        question=data.get("question", ""),
        slug=data.get("slug", ""),
        outcomes=tuple(parsed_outcomes),
        volume=float(data.get("volume", 0) or 0),
        liquidity=float(data.get("liquidity", 0) or 0),
        end_date=data.get("endDate", ""),
        active=data.get("active", True),
        category=data.get("category", ""),
    )
