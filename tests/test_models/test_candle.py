"""Tests for Candle frozen dataclass."""

from src.models.candle import Candle


def test_candle_creation():
    c = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    assert c.open == 0.50
    assert c.close == 0.53


def test_candle_is_bullish():
    bullish = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    assert bullish.is_bullish is True

    bearish = Candle(timestamp=1000, open=0.55, high=0.56, low=0.48, close=0.50, volume=100)
    assert bearish.is_bullish is False


def test_candle_body_size():
    c = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    assert abs(c.body_size - 0.03) < 0.001


def test_candle_range():
    c = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    assert abs(c.range - 0.07) < 0.001


def test_candle_typical_price():
    c = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    expected = (0.55 + 0.48 + 0.53) / 3.0
    assert abs(c.typical_price - expected) < 0.001


def test_candle_frozen():
    c = Candle(timestamp=1000, open=0.50, high=0.55, low=0.48, close=0.53, volume=100)
    try:
        c.close = 0.60
        assert False
    except AttributeError:
        pass
