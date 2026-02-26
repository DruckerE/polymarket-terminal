"""Tests for boundary suppression."""

from src.signals.boundary import boundary_suppression_factor, is_at_boundary


def test_normal_range_no_suppression():
    assert boundary_suppression_factor(0.50) == 1.0
    assert boundary_suppression_factor(0.30) == 1.0
    assert boundary_suppression_factor(0.70) == 1.0


def test_low_boundary_suppression():
    factor = boundary_suppression_factor(0.02)
    assert 0 < factor < 1
    assert factor < boundary_suppression_factor(0.04)


def test_high_boundary_suppression():
    factor = boundary_suppression_factor(0.98)
    assert 0 < factor < 1
    assert factor < boundary_suppression_factor(0.96)


def test_zero_price():
    assert boundary_suppression_factor(0.0) == 0.0


def test_one_price():
    assert boundary_suppression_factor(1.0) == 0.0


def test_is_at_boundary():
    assert is_at_boundary(0.02) is True
    assert is_at_boundary(0.98) is True
    assert is_at_boundary(0.50) is False
    assert is_at_boundary(0.10) is False
