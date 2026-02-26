"""Tests for Order Book Imbalance signal."""

import time

from src.data.market_cache import MarketState
from src.models.market import Market, Outcome
from src.models.orderbook import OrderBook, OrderLevel
from src.signals.obi import OBISignal


def _make_state(bids: list[tuple[float, float]], asks: list[tuple[float, float]]) -> MarketState:
    market = Market(condition_id="test", question="Test?", slug="test")
    book = OrderBook(
        token_id="tok",
        bids=tuple(OrderLevel(price=p, size=s) for p, s in bids),
        asks=tuple(OrderLevel(price=p, size=s) for p, s in asks),
        timestamp=time.time(),
    )
    return MarketState(market=market, orderbook=book)


def test_obi_bullish_imbalance():
    state = _make_state(
        bids=[(0.50, 200), (0.49, 150), (0.48, 100)],
        asks=[(0.52, 50), (0.53, 30), (0.54, 20)],
    )
    signal = OBISignal()
    result = signal.calculate(state)
    assert result.value > 0
    assert result.name == "OBI"


def test_obi_bearish_imbalance():
    state = _make_state(
        bids=[(0.50, 20), (0.49, 10)],
        asks=[(0.52, 200), (0.53, 150), (0.54, 100)],
    )
    signal = OBISignal()
    result = signal.calculate(state)
    assert result.value < 0


def test_obi_balanced():
    state = _make_state(
        bids=[(0.50, 100), (0.49, 100)],
        asks=[(0.52, 100), (0.53, 100)],
    )
    signal = OBISignal()
    result = signal.calculate(state)
    assert abs(result.value) < 0.01


def test_obi_no_orderbook():
    market = Market(condition_id="test", question="Test?", slug="test")
    state = MarketState(market=market)
    signal = OBISignal()
    result = signal.calculate(state)
    assert result.value == 0.0
    assert result.confidence == 0.0


def test_obi_empty_book():
    market = Market(condition_id="test", question="Test?", slug="test")
    book = OrderBook(token_id="tok")
    state = MarketState(market=market, orderbook=book)
    signal = OBISignal()
    result = signal.calculate(state)
    assert result.value == 0.0


def test_obi_weight():
    signal = OBISignal()
    assert signal.weight == 0.30
