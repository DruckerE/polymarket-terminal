"""Tests for Position, Trade, and PnLSnapshot frozen dataclasses."""

import time

from src.models.position import OutcomeType, PnLSnapshot, Position, Side, Trade


def test_trade_notional(sample_trade):
    assert abs(sample_trade.notional - 5.20) < 0.001


def test_trade_frozen(sample_trade):
    try:
        sample_trade.price = 0.60
        assert False
    except AttributeError:
        pass


def test_position_unrealized_pnl(sample_position):
    pnl = sample_position.unrealized_pnl
    expected = (0.55 - 0.52) * 10.0
    assert abs(pnl - expected) < 0.001


def test_position_unrealized_pnl_pct(sample_position):
    pct = sample_position.unrealized_pnl_pct
    expected = ((0.55 - 0.52) / 0.52) * 100.0
    assert abs(pct - expected) < 0.01


def test_position_notional(sample_position):
    assert abs(sample_position.notional - 5.50) < 0.001


def test_position_cost_basis(sample_position):
    assert abs(sample_position.cost_basis - 5.20) < 0.001


def test_pnl_snapshot_total():
    snap = PnLSnapshot(
        timestamp=time.time(),
        realized_pnl=5.0,
        unrealized_pnl=3.0,
        total_equity=1008.0,
    )
    assert snap.total_pnl == 8.0


def test_position_zero_entry():
    pos = Position(
        market_id="test",
        token_id="tok",
        outcome=OutcomeType.YES,
        size=10,
        avg_entry_price=0.0,
        current_price=0.5,
    )
    assert pos.unrealized_pnl_pct == 0.0
