"""Tests for OrderBook and OrderLevel frozen dataclasses."""

from src.models.orderbook import OrderBook, OrderLevel


def test_order_level_frozen():
    level = OrderLevel(price=0.50, size=100)
    assert level.price == 0.50
    assert level.size == 100
    try:
        level.price = 0.55
        assert False
    except AttributeError:
        pass


def test_orderbook_best_bid_ask(sample_orderbook):
    assert sample_orderbook.best_bid == 0.51
    assert sample_orderbook.best_ask == 0.53


def test_orderbook_spread(sample_orderbook):
    assert abs(sample_orderbook.spread - 0.02) < 0.001


def test_orderbook_midpoint(sample_orderbook):
    assert abs(sample_orderbook.midpoint - 0.52) < 0.001


def test_orderbook_imbalance(sample_orderbook):
    imbalance = sample_orderbook.imbalance
    assert -1.0 <= imbalance <= 1.0
    assert imbalance > 0  # More bid depth in fixture


def test_orderbook_depths(sample_orderbook):
    assert sample_orderbook.bid_depth == 580
    assert sample_orderbook.ask_depth == 390


def test_empty_orderbook():
    book = OrderBook(token_id="empty")
    assert book.best_bid == 0.0
    assert book.best_ask == 1.0
    assert book.spread == 1.0
    assert book.midpoint == 0.5
    assert book.imbalance == 0.0
