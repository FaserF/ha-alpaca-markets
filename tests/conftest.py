"""Fixtures for Alpaca Markets integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.alpaca_markets.const import (
    CONF_API_KEY_ID,
    CONF_API_SECRET_KEY,
    CONF_TRADING_MODE,
    DOMAIN,
    TRADING_MODE_PAPER,
)

MOCK_ACCOUNT = {
    "id": "mock_acc_12345",
    "account_number": "PA12345678",
    "status": "ACTIVE",
    "currency": "USD",
    "cash": "25000.50",
    "portfolio_value": "100000.75",
    "equity": "100000.75",
    "last_equity": "99500.00",
    "buying_power": "50000.00",
    "daytrading_buying_power": "100000.00",
    "long_market_value": "75000.25",
    "short_market_value": "0.0",
    "unrealized_pl": "500.75",
    "unrealized_plpc": "0.005",
    "realized_pl": "120.00",
    "realized_plpc": "0.0012",
    "initial_margin": "37500.00",
    "maintenance_margin": "18750.00",
    "daytrade_count": 1,
    "trading_blocked": False,
    "account_blocked": False,
    "account_restricted": False,
    "trade_suspended_by_user": False,
    "transfers_blocked": False,
    "pattern_day_trader": False,
    "shorting_enabled": True,
    "multiplier": "4",
}

MOCK_CLOCK = {
    "timestamp": "2026-10-20T09:30:00-04:00",
    "is_open": True,
    "next_open": "2026-10-21T09:30:00-04:00",
    "next_close": "2026-10-20T16:00:00-04:00",
}

MOCK_POSITIONS = [
    {
        "asset_id": "9048f725-b4af-4c4f-9e75-9c86a2f76c34",
        "symbol": "AAPL",
        "exchange": "NASDAQ",
        "asset_class": "us_equity",
        "qty": "10",
        "avg_entry_price": "150.00",
        "side": "long",
        "market_value": "1750.00",
        "cost_basis": "1500.00",
        "unrealized_pl": "250.00",
        "unrealized_plpc": "0.1667",
        "unrealized_intraday_pl": "25.00",
        "unrealized_intraday_plpc": "0.0145",
        "current_price": "175.00",
        "lastday_price": "172.50",
        "change_today": "0.0145",
    }
]

MOCK_ORDERS = [
    {
        "id": "6178c772-9b21-4f38-9cb5-1158f9c2d716",
        "client_order_id": "9048f725-b4af-4c4f-9e75-9c86a2f76c34",
        "created_at": "2026-10-20T09:35:00Z",
        "updated_at": "2026-10-20T09:35:00Z",
        "submitted_at": "2026-10-20T09:35:00Z",
        "symbol": "AAPL",
        "qty": "5",
        "filled_qty": "0",
        "type": "limit",
        "side": "buy",
        "time_in_force": "day",
        "limit_price": "170.00",
        "status": "new",
    }
]


@pytest.fixture
def mock_alpaca_client():
    """Mock Alpaca API client."""
    with patch(
        "custom_components.alpaca_markets.api.client.AlpacaAPIClient",
        autospec=True,
    ) as mock_client_cls:
        client = mock_client_cls.return_value
        client.get_account = AsyncMock(return_value=MOCK_ACCOUNT)
        client.get_clock = AsyncMock(return_value=MOCK_CLOCK)
        client.get_positions = AsyncMock(return_value=MOCK_POSITIONS)
        client.get_orders = AsyncMock(return_value=MOCK_ORDERS)
        client.cancel_all_orders = AsyncMock(return_value=None)
        client.close_all_positions = AsyncMock(return_value=None)
        client.place_order = AsyncMock(return_value={"id": "new_order_123"})
        client.cancel_order = AsyncMock(return_value=None)
        client.close_position = AsyncMock(return_value={})
        yield client
