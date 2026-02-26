"""Centralized in-memory state store for market data."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from src.models.candle import Candle
from src.models.market import Market
from src.models.orderbook import OrderBook
from src.models.position import PnLSnapshot, Position, Trade
from src.models.signal import CompositeScore


@dataclass
class MarketState:
    """State for a single market being tracked."""

    market: Market
    orderbook: OrderBook | None = None
    candles: tuple[Candle, ...] = field(default_factory=tuple)
    last_price: float = 0.0
    last_trade_time: float = 0.0
    composite_score: CompositeScore | None = None

    def with_orderbook(self, orderbook: OrderBook) -> MarketState:
        return MarketState(
            market=self.market,
            orderbook=orderbook,
            candles=self.candles,
            last_price=self.last_price,
            last_trade_time=self.last_trade_time,
            composite_score=self.composite_score,
        )

    def with_candle(self, candle: Candle) -> MarketState:
        return MarketState(
            market=self.market,
            orderbook=self.orderbook,
            candles=(*self.candles[-99:], candle),
            last_price=candle.close,
            last_trade_time=candle.timestamp,
            composite_score=self.composite_score,
        )

    def with_score(self, score: CompositeScore) -> MarketState:
        return MarketState(
            market=self.market,
            orderbook=self.orderbook,
            candles=self.candles,
            last_price=self.last_price,
            last_trade_time=self.last_trade_time,
            composite_score=score,
        )

    def with_price(self, price: float) -> MarketState:
        return MarketState(
            market=self.market,
            orderbook=self.orderbook,
            candles=self.candles,
            last_price=price,
            last_trade_time=time.time(),
            composite_score=self.composite_score,
        )


class MarketCache:
    """Centralized read/write cache for all market state."""

    def __init__(self) -> None:
        self._markets: dict[str, MarketState] = {}
        self._active_market_id: str = ""
        self._positions: dict[str, Position] = {}
        self._trades: list[Trade] = []
        self._pnl_history: list[PnLSnapshot] = []
        self._listeners: list[Callable[[], None]] = []
        self._connected = False

    @property
    def active_market_id(self) -> str:
        return self._active_market_id

    @active_market_id.setter
    def active_market_id(self, market_id: str) -> None:
        self._active_market_id = market_id
        self._notify()

    @property
    def active_state(self) -> MarketState | None:
        return self._markets.get(self._active_market_id)

    @property
    def connected(self) -> bool:
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        self._connected = value
        self._notify()

    @property
    def market_ids(self) -> list[str]:
        return list(self._markets.keys())

    @property
    def positions(self) -> dict[str, Position]:
        return dict(self._positions)

    @property
    def trades(self) -> tuple[Trade, ...]:
        return tuple(self._trades)

    @property
    def pnl_history(self) -> tuple[PnLSnapshot, ...]:
        return tuple(self._pnl_history)

    def add_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def get_state(self, market_id: str) -> MarketState | None:
        return self._markets.get(market_id)

    def set_market(self, market: Market) -> None:
        existing = self._markets.get(market.condition_id)
        if existing:
            self._markets[market.condition_id] = MarketState(
                market=market,
                orderbook=existing.orderbook,
                candles=existing.candles,
                last_price=existing.last_price,
                last_trade_time=existing.last_trade_time,
                composite_score=existing.composite_score,
            )
        else:
            self._markets[market.condition_id] = MarketState(market=market)
        self._notify()

    def update_orderbook(self, market_id: str, orderbook: OrderBook) -> None:
        state = self._markets.get(market_id)
        if state:
            self._markets[market_id] = state.with_orderbook(orderbook)
            self._notify()

    def add_candle(self, market_id: str, candle: Candle) -> None:
        state = self._markets.get(market_id)
        if state:
            self._markets[market_id] = state.with_candle(candle)
            self._notify()

    def update_score(self, market_id: str, score: CompositeScore) -> None:
        state = self._markets.get(market_id)
        if state:
            self._markets[market_id] = state.with_score(score)
            self._notify()

    def update_price(self, market_id: str, price: float) -> None:
        state = self._markets.get(market_id)
        if state:
            self._markets[market_id] = state.with_price(price)
            self._notify()

    def set_position(self, market_id: str, position: Position) -> None:
        self._positions[market_id] = position
        self._notify()

    def remove_position(self, market_id: str) -> None:
        self._positions.pop(market_id, None)
        self._notify()

    def add_trade(self, trade: Trade) -> None:
        self._trades.append(trade)
        self._notify()

    def add_pnl_snapshot(self, snapshot: PnLSnapshot) -> None:
        self._pnl_history.append(snapshot)
        self._notify()

    def all_states(self) -> list[MarketState]:
        return list(self._markets.values())

    def _notify(self) -> None:
        for listener in self._listeners:
            try:
                listener()
            except Exception:
                pass
