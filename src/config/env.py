"""Load and validate environment variables from .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class EnvConfig:
    """Validated environment configuration."""

    polymarket_pk: str
    api_key: str
    api_secret: str
    passphrase: str
    chain_id: int
    paper_balance: float

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret and self.passphrase)


def load_env(env_path: Path | None = None) -> EnvConfig:
    """Load .env file and return validated config.

    Missing credentials are allowed (paper mode only).
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    return EnvConfig(
        polymarket_pk=os.getenv("POLYMARKET_PK", ""),
        api_key=os.getenv("POLYMARKET_API_KEY", ""),
        api_secret=os.getenv("POLYMARKET_API_SECRET", ""),
        passphrase=os.getenv("POLYMARKET_PASSPHRASE", ""),
        chain_id=int(os.getenv("CHAIN_ID", "137")),
        paper_balance=float(os.getenv("PAPER_BALANCE", "1000.0")),
    )
