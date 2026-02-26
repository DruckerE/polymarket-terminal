"""Tests for arbitrage detection."""

from src.data.market_cache import MarketCache
from src.models.market import Market, Outcome
from src.trading.arbitrage import ArbitrageDetector


def test_detects_arb_opportunity():
    cache = MarketCache()
    market = Market(
        condition_id="arb-test",
        question="Arb market?",
        slug="arb",
        outcomes=(
            Outcome(token_id="t-yes", label="Yes", price=0.45),
            Outcome(token_id="t-no", label="No", price=0.48),
        ),
    )
    cache.set_market(market)

    detector = ArbitrageDetector(threshold=0.99)
    opps = detector.scan(cache)
    assert len(opps) == 1
    assert abs(opps[0].total_cost - 0.93) < 0.001
    assert abs(opps[0].profit_per_share - 0.07) < 0.001


def test_no_arb_when_total_above_threshold():
    cache = MarketCache()
    market = Market(
        condition_id="no-arb",
        question="No arb?",
        slug="noarb",
        outcomes=(
            Outcome(token_id="t-yes", label="Yes", price=0.52),
            Outcome(token_id="t-no", label="No", price=0.49),
        ),
    )
    cache.set_market(market)

    detector = ArbitrageDetector(threshold=0.99)
    opps = detector.scan(cache)
    assert len(opps) == 0


def test_arb_sorted_by_profit():
    cache = MarketCache()
    m1 = Market(
        condition_id="m1",
        question="M1?",
        slug="m1",
        outcomes=(
            Outcome(token_id="t1y", label="Yes", price=0.40),
            Outcome(token_id="t1n", label="No", price=0.45),
        ),
    )
    m2 = Market(
        condition_id="m2",
        question="M2?",
        slug="m2",
        outcomes=(
            Outcome(token_id="t2y", label="Yes", price=0.45),
            Outcome(token_id="t2n", label="No", price=0.50),
        ),
    )
    cache.set_market(m1)
    cache.set_market(m2)

    detector = ArbitrageDetector(threshold=0.99)
    opps = detector.scan(cache)
    assert len(opps) == 2
    assert opps[0].profit_per_share >= opps[1].profit_per_share
