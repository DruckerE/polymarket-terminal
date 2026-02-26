"""Frozen dataclass settings for trading, signals, and application config."""

from __future__ import annotations

from dataclasses import dataclass

from src.config.constants import (
    CANDLE_INTERVAL_SECONDS,
    DEFAULT_PAPER_BALANCE,
    KELLY_FRACTION,
    MAX_DRAWDOWN_PCT,
    MAX_POSITION_PCT,
    MAX_POSITIONS,
    SIGNAL_RECALC_SECONDS,
)


@dataclass(frozen=True)
class SignalWeights:
    """Weight configuration for composite signal scoring."""

    obi: float = 0.30
    vwap: float = 0.20
    rsi: float = 0.15
    macd: float = 0.10
    bollinger: float = 0.10
    obv: float = 0.10
    volume: float = 0.05

    def validate(self) -> None:
        total = self.obi + self.vwap + self.rsi + self.macd + self.bollinger + self.obv + self.volume
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Signal weights must sum to 1.0, got {total:.4f}")


@dataclass(frozen=True)
class TradingSettings:
    """Risk management and trading parameters."""

    kelly_fraction: float = KELLY_FRACTION
    max_position_pct: float = MAX_POSITION_PCT
    max_positions: int = MAX_POSITIONS
    max_drawdown_pct: float = MAX_DRAWDOWN_PCT
    stop_loss_atr_mult: float = 2.0
    candle_interval: int = CANDLE_INTERVAL_SECONDS
    signal_recalc_interval: int = SIGNAL_RECALC_SECONDS
    paper_balance: float = DEFAULT_PAPER_BALANCE
    arb_threshold: float = 0.99


@dataclass(frozen=True)
class AppSettings:
    """Top-level application configuration."""

    trading: TradingSettings
    weights: SignalWeights
    live_mode: bool = False
    debug: bool = False

    @staticmethod
    def default() -> AppSettings:
        weights = SignalWeights()
        weights.validate()
        return AppSettings(
            trading=TradingSettings(),
            weights=weights,
        )
