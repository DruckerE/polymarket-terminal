"""Tests for ATR-based stop-loss calculation."""

from src.models.candle import Candle
from src.models.position import OutcomeType, Position
from src.trading.stop_loss import calculate_atr, calculate_stop_loss, should_stop_out


def test_atr_calculation(sample_candles):
    atr = calculate_atr(sample_candles)
    assert atr > 0


def test_atr_insufficient_data():
    atr = calculate_atr([])
    assert atr == 0.0


def test_stop_loss_calculation(sample_candles, sample_position):
    stop = calculate_stop_loss(sample_position, sample_candles, atr_multiplier=2.0)
    assert 0.0 <= stop <= 1.0
    assert stop < sample_position.avg_entry_price


def test_stop_loss_no_candles(sample_position):
    stop = calculate_stop_loss(sample_position, [], atr_multiplier=2.0)
    assert stop == sample_position.avg_entry_price - 0.05


def test_should_stop_out_no_stop():
    pos = Position(
        market_id="m", token_id="t", outcome=OutcomeType.YES,
        size=10, avg_entry_price=0.50, current_price=0.40,
    )
    assert should_stop_out(pos, 0.40) is False


def test_should_stop_out_triggered():
    pos = Position(
        market_id="m", token_id="t", outcome=OutcomeType.YES,
        size=10, avg_entry_price=0.50, current_price=0.40, stop_loss=0.45,
    )
    assert should_stop_out(pos, 0.40) is True


def test_should_stop_out_not_triggered():
    pos = Position(
        market_id="m", token_id="t", outcome=OutcomeType.YES,
        size=10, avg_entry_price=0.50, current_price=0.48, stop_loss=0.45,
    )
    assert should_stop_out(pos, 0.48) is False
