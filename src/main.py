"""Entry point for the Polymarket Terminal application."""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="polymarket-terminal",
        description="Bloomberg Terminal-style TUI for Polymarket prediction markets",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Enable live trading mode (requires API credentials)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    parser.add_argument(
        "--balance",
        type=float,
        default=1000.0,
        help="Starting paper balance (default: 1000.0)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    from src.config.env import load_env
    from src.config.settings import AppSettings, SignalWeights, TradingSettings
    from src.ui.app import PolymarketTerminal

    env = load_env()

    if args.live and not env.has_credentials:
        print("Error: Live mode requires API credentials in .env file")
        sys.exit(1)

    weights = SignalWeights()
    weights.validate()

    trading = TradingSettings(paper_balance=args.balance)
    settings = AppSettings(
        trading=trading,
        weights=weights,
        live_mode=args.live,
        debug=args.debug,
    )

    app = PolymarketTerminal(settings)
    app.run()


if __name__ == "__main__":
    main()
