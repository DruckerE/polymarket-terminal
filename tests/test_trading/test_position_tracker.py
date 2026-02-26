"""Tests for position tracking and P&L calculation."""

import time

from src.models.position import OutcomeType, Side, Trade
from src.trading.position_tracker import PositionTracker


def test_open_position():
    tracker = PositionTracker()
    trade = Trade(
        trade_id="t1", market_id="m1", token_id="tok1",
        side=Side.BUY, outcome=OutcomeType.YES,
        price=0.50, size=10, timestamp=time.time(),
    )
    tracker.process_trade(trade)
    assert tracker.open_count == 1
    assert "m1:YES" in tracker.positions


def test_close_position():
    tracker = PositionTracker()
    buy = Trade(
        trade_id="t1", market_id="m1", token_id="tok1",
        side=Side.BUY, outcome=OutcomeType.YES,
        price=0.50, size=10, timestamp=time.time(),
    )
    sell = Trade(
        trade_id="t2", market_id="m1", token_id="tok1",
        side=Side.SELL, outcome=OutcomeType.YES,
        price=0.60, size=10, timestamp=time.time(),
    )
    tracker.process_trade(buy)
    tracker.process_trade(sell)
    assert tracker.open_count == 0
    assert tracker.realized_pnl > 0


def test_partial_close():
    tracker = PositionTracker()
    buy = Trade(
        trade_id="t1", market_id="m1", token_id="tok1",
        side=Side.BUY, outcome=OutcomeType.YES,
        price=0.50, size=10, timestamp=time.time(),
    )
    sell = Trade(
        trade_id="t2", market_id="m1", token_id="tok1",
        side=Side.SELL, outcome=OutcomeType.YES,
        price=0.55, size=5, timestamp=time.time(),
    )
    tracker.process_trade(buy)
    tracker.process_trade(sell)
    assert tracker.open_count == 1
    pos = tracker.positions["m1:YES"]
    assert pos.size == 5.0


def test_snapshot(sample_trade):
    tracker = PositionTracker(starting_equity=1000.0)
    tracker.process_trade(sample_trade)
    snap = tracker.snapshot(balance=994.80)
    assert snap.total_equity > 0
    assert snap.total_trades == 0  # no closed trades yet


def test_add_to_position():
    tracker = PositionTracker()
    buy1 = Trade(
        trade_id="t1", market_id="m1", token_id="tok1",
        side=Side.BUY, outcome=OutcomeType.YES,
        price=0.50, size=10, timestamp=time.time(),
    )
    buy2 = Trade(
        trade_id="t2", market_id="m1", token_id="tok1",
        side=Side.BUY, outcome=OutcomeType.YES,
        price=0.55, size=10, timestamp=time.time(),
    )
    tracker.process_trade(buy1)
    tracker.process_trade(buy2)
    assert tracker.open_count == 1
    pos = tracker.positions["m1:YES"]
    assert pos.size == 20.0
    assert abs(pos.avg_entry_price - 0.525) < 0.001
