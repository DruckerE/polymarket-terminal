"""API URLs, color palette, rate limits, and application constants."""

from __future__ import annotations

# ── Polymarket API endpoints ───────────────────────────────────────────
CLOB_BASE_URL = "https://clob.polymarket.com"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# ── Rate limits (requests per second) ─────────────────────────────────
CLOB_RATE_LIMIT = 10
GAMMA_RATE_LIMIT = 5

# ── Bloomberg terminal color palette ──────────────────────────────────
COLOR_BG = "#000000"
COLOR_AMBER = "#FFB000"
COLOR_GREEN = "#00FF41"
COLOR_RED = "#FF073A"
COLOR_DIM = "#555555"
COLOR_CYAN = "#00D4FF"
COLOR_WHITE = "#E0E0E0"
COLOR_BORDER = "#333333"
COLOR_HEADER_BG = "#1A1A2E"
COLOR_HIGHLIGHT = "#FFB00033"

# ── Signal thresholds ─────────────────────────────────────────────────
BUY_THRESHOLD = 0.1
SELL_THRESHOLD = -0.1
BOUNDARY_LOW = 0.05
BOUNDARY_HIGH = 0.95

# ── Timeframes ────────────────────────────────────────────────────────
CANDLE_INTERVAL_SECONDS = 300  # 5 minutes
SIGNAL_RECALC_SECONDS = 5
UI_REFRESH_SECONDS = 1

# ── Trading defaults ─────────────────────────────────────────────────
DEFAULT_PAPER_BALANCE = 1000.0
MAX_POSITIONS = 5
MAX_DRAWDOWN_PCT = 0.20
KELLY_FRACTION = 0.25
MAX_POSITION_PCT = 0.10

# ── WebSocket ─────────────────────────────────────────────────────────
WS_RECONNECT_DELAY = 3.0
WS_PING_INTERVAL = 30.0
WS_MAX_RETRIES = 10

# ── Chain ─────────────────────────────────────────────────────────────
POLYGON_CHAIN_ID = 137
