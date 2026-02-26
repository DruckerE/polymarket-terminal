"""Tests for risk management: Kelly Criterion, position limits, drawdown."""

from src.config.settings import TradingSettings
from src.trading.risk import (
    calculate_drawdown,
    calculate_position_size,
    check_drawdown_circuit_breaker,
    kelly_criterion,
)


def test_kelly_positive_edge():
    fraction = kelly_criterion(win_prob=0.6, win_return=1.0, loss_return=1.0, fraction=1.0)
    assert fraction > 0
    assert abs(fraction - 0.2) < 0.01


def test_kelly_no_edge():
    fraction = kelly_criterion(win_prob=0.5, win_return=1.0, loss_return=1.0, fraction=1.0)
    assert fraction == 0.0


def test_kelly_negative_edge():
    fraction = kelly_criterion(win_prob=0.3, win_return=1.0, loss_return=1.0, fraction=1.0)
    assert fraction == 0.0


def test_kelly_quarter():
    full = kelly_criterion(win_prob=0.6, win_return=1.0, loss_return=1.0, fraction=1.0)
    quarter = kelly_criterion(win_prob=0.6, win_return=1.0, loss_return=1.0, fraction=0.25)
    assert abs(quarter - full * 0.25) < 0.001


def test_kelly_invalid_inputs():
    assert kelly_criterion(0, 1.0, 1.0) == 0.0
    assert kelly_criterion(1, 1.0, 1.0) == 0.0
    assert kelly_criterion(0.5, 0, 1.0) == 0.0
    assert kelly_criterion(0.5, 1.0, 0) == 0.0


def test_position_sizing():
    settings = TradingSettings()
    sizing = calculate_position_size(
        score=0.5, price=0.50, equity=1000.0, settings=settings
    )
    assert sizing.size >= 0
    assert sizing.kelly_full >= 0
    assert sizing.max_allowed == 100.0  # 10% of 1000


def test_position_sizing_max_positions():
    settings = TradingSettings(max_positions=5)
    sizing = calculate_position_size(
        score=0.5, price=0.50, equity=1000.0, settings=settings, open_positions=5
    )
    assert sizing.size == 0.0
    assert "Max positions" in sizing.reason


def test_position_sizing_invalid_price():
    settings = TradingSettings()
    sizing = calculate_position_size(score=0.5, price=0.0, equity=1000.0, settings=settings)
    assert sizing.size == 0.0


def test_circuit_breaker_no_trigger():
    assert check_drawdown_circuit_breaker(950.0, 1000.0, 0.20) is False


def test_circuit_breaker_trigger():
    assert check_drawdown_circuit_breaker(790.0, 1000.0, 0.20) is True


def test_calculate_drawdown():
    equity = [1000, 1050, 1020, 980, 1100, 900, 1050]
    dd = calculate_drawdown(equity)
    # Peak was 1100, trough was 900 = 18.18% drawdown
    assert abs(dd - (1100 - 900) / 1100) < 0.01


def test_calculate_drawdown_empty():
    assert calculate_drawdown([]) == 0.0
    assert calculate_drawdown([1000]) == 0.0
