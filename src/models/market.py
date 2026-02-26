"""Market and Outcome frozen dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Outcome:
    """A single outcome (YES/NO) of a market."""

    token_id: str
    label: str
    price: float = 0.0


@dataclass(frozen=True)
class Market:
    """A Polymarket prediction market."""

    condition_id: str
    question: str
    slug: str
    outcomes: tuple[Outcome, ...] = field(default_factory=tuple)
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: str = ""
    active: bool = True
    category: str = ""

    @property
    def yes_outcome(self) -> Outcome | None:
        for outcome in self.outcomes:
            if outcome.label.upper() == "YES":
                return outcome
        return self.outcomes[0] if self.outcomes else None

    @property
    def no_outcome(self) -> Outcome | None:
        for outcome in self.outcomes:
            if outcome.label.upper() == "NO":
                return outcome
        return self.outcomes[1] if len(self.outcomes) > 1 else None

    @property
    def yes_price(self) -> float:
        outcome = self.yes_outcome
        return outcome.price if outcome else 0.0

    @property
    def no_price(self) -> float:
        outcome = self.no_outcome
        return outcome.price if outcome else 0.0
