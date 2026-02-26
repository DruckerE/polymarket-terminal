"""Save and restore session state to JSON."""

from __future__ import annotations

import json
from pathlib import Path


class SessionState:
    """Persists session state (watchlist, settings) to JSON."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("session_state.json")

    def save(self, state: dict) -> None:
        """Save session state to disk."""
        with open(self._path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def load(self) -> dict:
        """Load session state from disk. Returns empty dict if no saved state."""
        if not self._path.exists():
            return {}

        try:
            with open(self._path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def save_watchlist(self, market_ids: list[str]) -> None:
        """Save watchlist to session state."""
        state = self.load()
        state["watchlist"] = market_ids
        self.save(state)

    def load_watchlist(self) -> list[str]:
        """Load watchlist from session state."""
        state = self.load()
        return state.get("watchlist", [])
