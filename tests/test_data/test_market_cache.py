"""Tests for centralized market cache."""

import time

from src.data.market_cache import MarketCache
from src.models.candle import Candle
from src.models.market import Market, Outcome
from src.models.orderbook import OrderBook, OrderLevel
from src.models.signal import CompositeScore, SignalDirection


def test_set_and_get_market():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)
    state = cache.get_state("c1")
    assert state is not None
    assert state.market.question == "Test?"


def test_active_market():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)
    cache.active_market_id = "c1"
    assert cache.active_state is not None
    assert cache.active_state.market.condition_id == "c1"


def test_update_orderbook():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)

    book = OrderBook(
        token_id="t1",
        bids=(OrderLevel(price=0.50, size=100),),
        asks=(OrderLevel(price=0.52, size=80),),
    )
    cache.update_orderbook("c1", book)

    state = cache.get_state("c1")
    assert state.orderbook is not None
    assert state.orderbook.best_bid == 0.50


def test_add_candle():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)

    candle = Candle(timestamp=time.time(), open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    cache.add_candle("c1", candle)

    state = cache.get_state("c1")
    assert len(state.candles) == 1


def test_update_score():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)

    score = CompositeScore(score=0.5, direction=SignalDirection.BUY, signals=())
    cache.update_score("c1", score)

    state = cache.get_state("c1")
    assert state.composite_score is not None
    assert state.composite_score.score == 0.5


def test_listener_called():
    cache = MarketCache()
    calls = []
    cache.add_listener(lambda: calls.append(1))

    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)
    assert len(calls) == 1


def test_connected_state():
    cache = MarketCache()
    assert cache.connected is False
    cache.connected = True
    assert cache.connected is True


def test_candle_limit():
    cache = MarketCache()
    market = Market(condition_id="c1", question="Test?", slug="test")
    cache.set_market(market)

    for i in range(150):
        candle = Candle(
            timestamp=time.time() + i,
            open=0.50, high=0.55, low=0.48, close=0.53, volume=10,
        )
        cache.add_candle("c1", candle)

    state = cache.get_state("c1")
    assert len(state.candles) == 100  # Capped at 100
