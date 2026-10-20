"""Tests for Alpaca Markets sensors and entities."""

from __future__ import annotations

import pytest
from custom_components.alpaca_markets.coordinator import (
    AlpacaAccountData,
    AlpacaClockData,
    AlpacaData,
    AlpacaOrderSummary,
    AlpacaPositionSummary,
    _parse_account,
    _parse_clock,
    _parse_orders,
    _parse_positions,
)
from tests.conftest import MOCK_ACCOUNT, MOCK_CLOCK, MOCK_ORDERS, MOCK_POSITIONS


def test_parse_account() -> None:
    """Test parsing account data."""
    account = _parse_account(MOCK_ACCOUNT)
    assert account.account_id == "mock_acc_12345"
    assert account.cash == 25000.50
    assert account.portfolio_value == 100000.75
    assert account.equity == 100000.75
    assert account.buying_power == 50000.00
    assert account.daytrade_count == 1
    assert account.trading_blocked is False
    assert account.pattern_day_trader is False
    assert account.shorting_enabled is True


def test_parse_clock() -> None:
    """Test parsing market clock data."""
    clock = _parse_clock(MOCK_CLOCK)
    assert clock.is_open is True
    assert clock.next_open == "2026-10-21T09:30:00-04:00"
    assert clock.next_close == "2026-10-20T16:00:00-04:00"


def test_parse_positions() -> None:
    """Test parsing positions data."""
    positions = _parse_positions(MOCK_POSITIONS)
    assert positions.count == 1
    assert positions.total_market_value == 1750.00
    assert positions.total_unrealized_pl == 250.00


def test_parse_orders() -> None:
    """Test parsing orders data."""
    orders = _parse_orders(MOCK_ORDERS)
    assert orders.open_count == 1
    assert len(orders.orders) == 1
