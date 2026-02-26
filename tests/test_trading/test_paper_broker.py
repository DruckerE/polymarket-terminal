"""Tests for paper trade simulator."""

from src.models.order import OrderRequest, OrderType
from src.models.position import OutcomeType, Side
from src.trading.paper_broker import PaperBroker


def test_initial_balance():
    broker = PaperBroker(starting_balance=500.0)
    assert broker.balance == 500.0


def test_buy_deducts_balance():
    broker = PaperBroker(starting_balance=1000.0)
    request = OrderRequest(
        market_id="m1",
        token_id="t1",
        side=Side.BUY,
        outcome=OutcomeType.YES,
        price=0.50,
        size=10,
    )
    response = broker.place_order(request)
    assert response.success is True
    assert abs(broker.balance - 995.0) < 0.001


def test_sell_adds_balance():
    broker = PaperBroker(starting_balance=1000.0)
    request = OrderRequest(
        market_id="m1",
        token_id="t1",
        side=Side.SELL,
        outcome=OutcomeType.YES,
        price=0.60,
        size=10,
    )
    response = broker.place_order(request)
    assert response.success is True
    assert abs(broker.balance - 1006.0) < 0.001


def test_insufficient_balance():
    broker = PaperBroker(starting_balance=1.0)
    request = OrderRequest(
        market_id="m1",
        token_id="t1",
        side=Side.BUY,
        outcome=OutcomeType.YES,
        price=0.50,
        size=100,
    )
    response = broker.place_order(request)
    assert response.success is False
    assert "Insufficient" in response.error


def test_trade_recorded():
    broker = PaperBroker()
    request = OrderRequest(
        market_id="m1",
        token_id="t1",
        side=Side.BUY,
        outcome=OutcomeType.YES,
        price=0.50,
        size=5,
    )
    broker.place_order(request)
    assert len(broker.trades) == 1
    assert broker.trades[0].is_paper is True


def test_reset():
    broker = PaperBroker(starting_balance=1000.0)
    request = OrderRequest(
        market_id="m1",
        token_id="t1",
        side=Side.BUY,
        outcome=OutcomeType.YES,
        price=0.50,
        size=10,
    )
    broker.place_order(request)
    broker.reset()
    assert broker.balance == 1000.0
    assert len(broker.trades) == 0
