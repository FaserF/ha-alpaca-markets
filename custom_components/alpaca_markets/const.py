"""Constants for the Alpaca Markets integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "alpaca_markets"
DOCS_URL: Final = "https://github.com/FaserF/ha-alpaca-markets"

# Configuration keys
CONF_API_KEY_ID: Final = "api_key_id"
CONF_API_SECRET_KEY: Final = "api_secret_key"
CONF_TRADING_MODE: Final = "trading_mode"
CONF_UPDATE_INTERVAL: Final = "update_interval"

# Trading modes
TRADING_MODE_PAPER: Final = "paper"
TRADING_MODE_LIVE: Final = "live"

# API base URLs
API_BASE_URLS: dict[str, str] = {
    TRADING_MODE_PAPER: "https://paper-api.alpaca.markets/v2",
    TRADING_MODE_LIVE: "https://api.alpaca.markets/v2",
}

# Internal data keys
DATA_COORDINATOR: Final = "coordinator"
DATA_CLIENT: Final = "client"

# Defaults
DEFAULT_UPDATE_INTERVAL: Final = 60
DEFAULT_TRADING_MODE: Final = TRADING_MODE_PAPER

# Platforms
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
]

# API Header names
HEADER_KEY_ID: Final = "APCA-API-KEY-ID"
HEADER_SECRET_KEY: Final = "APCA-API-SECRET-KEY"

# Services
SERVICE_PLACE_ORDER: Final = "place_order"
SERVICE_CANCEL_ORDER: Final = "cancel_order"
SERVICE_CLOSE_POSITION: Final = "close_position"

# Order sides
ORDER_SIDE_BUY: Final = "buy"
ORDER_SIDE_SELL: Final = "sell"

# Order types
ORDER_TYPE_MARKET: Final = "market"
ORDER_TYPE_LIMIT: Final = "limit"
ORDER_TYPE_STOP: Final = "stop"
ORDER_TYPE_STOP_LIMIT: Final = "stop_limit"

# Time in force
TIME_IN_FORCE_DAY: Final = "day"
TIME_IN_FORCE_GTC: Final = "gtc"
TIME_IN_FORCE_IOC: Final = "ioc"
TIME_IN_FORCE_FOK: Final = "fok"
