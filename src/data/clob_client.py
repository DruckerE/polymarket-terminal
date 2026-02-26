"""CLOB API client for orderbook, pricing, and order operations."""

from __future__ import annotations

import httpx

from src.config.constants import CLOB_BASE_URL
from src.models.orderbook import OrderBook, OrderLevel


async def get_orderbook(token_id: str) -> OrderBook:
    """Fetch the current order book for a token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{CLOB_BASE_URL}/book",
            params={"token_id": token_id},
        )
        resp.raise_for_status()
        data = resp.json()
        return _parse_orderbook(token_id, data)


async def get_price(token_id: str) -> float:
    """Get the current midpoint price for a token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{CLOB_BASE_URL}/price",
            params={"token_id": token_id, "side": "buy"},
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0))


async def get_midpoint(token_id: str) -> float:
    """Get the midpoint price for a token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{CLOB_BASE_URL}/midpoint",
            params={"token_id": token_id},
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("mid", 0))


async def get_last_trade_price(token_id: str) -> float:
    """Get the last trade price for a token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{CLOB_BASE_URL}/last-trade-price",
            params={"token_id": token_id},
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0))


async def get_prices_history(
    token_id: str,
    interval: str = "5m",
    fidelity: int = 60,
) -> list[dict]:
    """Get historical price data."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{CLOB_BASE_URL}/prices-history",
            params={
                "market": token_id,
                "interval": interval,
                "fidelity": fidelity,
            },
        )
        resp.raise_for_status()
        return resp.json().get("history", [])


def _parse_orderbook(token_id: str, data: dict) -> OrderBook:
    """Parse raw API response into OrderBook dataclass."""
    bids = tuple(
        OrderLevel(price=float(b.get("price", 0)), size=float(b.get("size", 0)))
        for b in data.get("bids", [])
    )
    asks = tuple(
        OrderLevel(price=float(a.get("price", 0)), size=float(a.get("size", 0)))
        for a in data.get("asks", [])
    )

    sorted_bids = tuple(sorted(bids, key=lambda x: x.price, reverse=True))
    sorted_asks = tuple(sorted(asks, key=lambda x: x.price))

    return OrderBook(
        token_id=token_id,
        bids=sorted_bids,
        asks=sorted_asks,
    )
