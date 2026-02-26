"""Shared test fixtures for the Polymarket Terminal test suite."""

from __future__ import annotations

import time

import pytest

from src.config.settings import AppSettings, SignalWeights, TradingSettings
from src.data.market_cache import MarketCache
from src.models.candle import Candle
from src.models.market import Market, Outcome
from src.models.orderbook import OrderBook, OrderLevel
from src.models.position import OutcomeType, Position, Side, Trade


@pytest.fixture
def settings() -> AppSettings:
    return AppSettings.default()


@pytest.fixture
def trading_settings() -> TradingSettings:
    return TradingSettings()


@pytest.fixture
def signal_weights() -> SignalWeights:
    return SignalWeights()


@pytest.fixture
def cache() -> MarketCache:
    return MarketCache()


@pytest.fixture
def sample_market() -> Market:
    return Market(
        condition_id="test-condition-123",
        question="Will ETH go up?",
        slug="eth-up",
        outcomes=(
            Outcome(token_id="token-yes-123", label="Yes", price=0.52),
            Outcome(token_id="token-no-123", label="No", price=0.48),
        ),
        volume=50000.0,
        liquidity=10000.0,
        active=True,
    )


@pytest.fixture
def sample_orderbook() -> OrderBook:
    return OrderBook(
        token_id="token-yes-123",
        bids=(
            OrderLevel(price=0.51, size=100),
            OrderLevel(price=0.50, size=200),
            OrderLevel(price=0.49, size=150),
            OrderLevel(price=0.48, size=80),
            OrderLevel(price=0.47, size=50),
        ),
        asks=(
            OrderLevel(price=0.53, size=80),
            OrderLevel(price=0.54, size=120),
            OrderLevel(price=0.55, size=90),
            OrderLevel(price=0.56, size=60),
            OrderLevel(price=0.57, size=40),
        ),
        timestamp=time.time(),
    )


@pytest.fixture
def sample_candles() -> list[Candle]:
    """Generate 30 sample candles with realistic price movement."""
    base_time = time.time() - 300 * 30
    candles = []
    price = 0.50
    for i in range(30):
        import random

        random.seed(42 + i)
        change = random.uniform(-0.02, 0.02)
        open_p = price
        close_p = max(0.01, min(0.99, price + change))
        high_p = max(open_p, close_p) + random.uniform(0, 0.01)
        low_p = min(open_p, close_p) - random.uniform(0, 0.01)
        low_p = max(0.01, low_p)
        volume = random.uniform(10, 200)

        candles.append(
            Candle(
                timestamp=base_time + i * 300,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=volume,
                trade_count=int(volume / 5),
            )
        )
        price = close_p

    return candles


@pytest.fixture
def sample_trade() -> Trade:
    return Trade(
        trade_id="trade-001",
        market_id="test-condition-123",
        token_id="token-yes-123",
        side=Side.BUY,
        outcome=OutcomeType.YES,
        price=0.52,
        size=10.0,
        timestamp=time.time(),
        is_paper=True,
    )


@pytest.fixture
def sample_position() -> Position:
    return Position(
        market_id="test-condition-123",
        token_id="token-yes-123",
        outcome=OutcomeType.YES,
        size=10.0,
        avg_entry_price=0.52,
        current_price=0.55,
    )
