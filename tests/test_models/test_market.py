"""Tests for Market and Outcome frozen dataclasses."""

from src.models.market import Market, Outcome


def test_outcome_creation():
    outcome = Outcome(token_id="tok-1", label="Yes", price=0.65)
    assert outcome.token_id == "tok-1"
    assert outcome.label == "Yes"
    assert outcome.price == 0.65


def test_outcome_is_frozen():
    outcome = Outcome(token_id="tok-1", label="Yes", price=0.65)
    try:
        outcome.price = 0.70
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_market_yes_no_outcomes(sample_market):
    assert sample_market.yes_outcome is not None
    assert sample_market.yes_outcome.label == "Yes"
    assert sample_market.no_outcome is not None
    assert sample_market.no_outcome.label == "No"


def test_market_prices(sample_market):
    assert sample_market.yes_price == 0.52
    assert sample_market.no_price == 0.48


def test_market_is_frozen(sample_market):
    try:
        sample_market.question = "changed"
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_market_no_outcomes():
    market = Market(condition_id="empty", question="Test?", slug="test")
    assert market.yes_outcome is None
    assert market.no_outcome is None
    assert market.yes_price == 0.0
    assert market.no_price == 0.0
