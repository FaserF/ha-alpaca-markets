"""Data coordinator for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api.client import AlpacaAPIClient
from .api.exceptions import (
    AlpacaAuthError,
    AlpacaConnectionError,
    AlpacaError,
)
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class AlpacaAccountData:
    """Parsed Alpaca account data."""

    account_id: str = ""
    account_number: str = ""
    status: str = ""
    currency: str = "USD"
    cash: float = 0.0
    portfolio_value: float = 0.0
    equity: float = 0.0
    last_equity: float = 0.0
    buying_power: float = 0.0
    daytrading_buying_power: float = 0.0
    long_market_value: float = 0.0
    short_market_value: float = 0.0
    unrealized_pl: float = 0.0
    unrealized_plpc: float = 0.0
    realized_pl: float = 0.0
    realized_plpc: float = 0.0
    initial_margin: float = 0.0
    maintenance_margin: float = 0.0
    daytrade_count: int = 0
    trading_blocked: bool = False
    account_blocked: bool = False
    account_restricted: bool = False
    trade_suspended_by_user: bool = False
    transfers_blocked: bool = False
    pattern_day_trader: bool = False
    shorting_enabled: bool = False
    multiplier: str = "1"


@dataclass
class AlpacaClockData:
    """Parsed market clock data."""

    timestamp: str = ""
    is_open: bool = False
    next_open: str = ""
    next_close: str = ""


@dataclass
class AlpacaPositionSummary:
    """Summary of all open positions."""

    count: int = 0
    total_market_value: float = 0.0
    total_unrealized_pl: float = 0.0
    total_unrealized_plpc: float = 0.0
    positions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AlpacaOrderSummary:
    """Summary of orders."""

    open_count: int = 0
    orders: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AlpacaData:
    """Aggregated data fetched from Alpaca API."""

    account: AlpacaAccountData = field(default_factory=AlpacaAccountData)
    clock: AlpacaClockData = field(default_factory=AlpacaClockData)
    positions: AlpacaPositionSummary = field(default_factory=AlpacaPositionSummary)
    orders: AlpacaOrderSummary = field(default_factory=AlpacaOrderSummary)
    last_updated: datetime | None = None


def _parse_float(value: Any, default: float = 0.0) -> float:
    """Safely parse a float value."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _parse_account(raw: dict[str, Any]) -> AlpacaAccountData:
    """Parse raw account API response into AlpacaAccountData."""
    return AlpacaAccountData(
        account_id=raw.get("id", ""),
        account_number=raw.get("account_number", ""),
        status=raw.get("status", ""),
        currency=raw.get("currency", "USD"),
        cash=_parse_float(raw.get("cash")),
        portfolio_value=_parse_float(raw.get("portfolio_value")),
        equity=_parse_float(raw.get("equity")),
        last_equity=_parse_float(raw.get("last_equity")),
        buying_power=_parse_float(raw.get("buying_power")),
        daytrading_buying_power=_parse_float(raw.get("daytrading_buying_power")),
        long_market_value=_parse_float(raw.get("long_market_value")),
        short_market_value=_parse_float(raw.get("short_market_value")),
        unrealized_pl=_parse_float(raw.get("unrealized_pl")),
        unrealized_plpc=_parse_float(raw.get("unrealized_plpc")),
        realized_pl=_parse_float(raw.get("realized_pl")),
        realized_plpc=_parse_float(raw.get("realized_plpc")),
        initial_margin=_parse_float(raw.get("initial_margin")),
        maintenance_margin=_parse_float(raw.get("maintenance_margin")),
        daytrade_count=int(raw.get("daytrade_count", 0)),
        trading_blocked=bool(raw.get("trading_blocked", False)),
        account_blocked=bool(raw.get("account_blocked", False)),
        account_restricted=bool(raw.get("account_restricted", False)),
        trade_suspended_by_user=bool(raw.get("trade_suspended_by_user", False)),
        transfers_blocked=bool(raw.get("transfers_blocked", False)),
        pattern_day_trader=bool(raw.get("pattern_day_trader", False)),
        shorting_enabled=bool(raw.get("shorting_enabled", False)),
        multiplier=str(raw.get("multiplier", "1")),
    )


def _parse_clock(raw: dict[str, Any]) -> AlpacaClockData:
    """Parse raw clock API response into AlpacaClockData."""
    return AlpacaClockData(
        timestamp=raw.get("timestamp", ""),
        is_open=bool(raw.get("is_open", False)),
        next_open=raw.get("next_open", ""),
        next_close=raw.get("next_close", ""),
    )


def _parse_positions(raw_list: list[dict[str, Any]]) -> AlpacaPositionSummary:
    """Parse raw positions list into AlpacaPositionSummary."""
    total_mv = sum(_parse_float(p.get("market_value")) for p in raw_list)
    total_pl = sum(_parse_float(p.get("unrealized_pl")) for p in raw_list)
    total_plpc = (
        (total_pl / (total_mv - total_pl)) if (total_mv - total_pl) != 0 else 0.0
    )
    return AlpacaPositionSummary(
        count=len(raw_list),
        total_market_value=total_mv,
        total_unrealized_pl=total_pl,
        total_unrealized_plpc=total_plpc,
        positions=raw_list,
    )


def _parse_orders(raw_list: list[dict[str, Any]]) -> AlpacaOrderSummary:
    """Parse raw orders list into AlpacaOrderSummary."""
    return AlpacaOrderSummary(
        open_count=len(raw_list),
        orders=raw_list,
    )


class AlpacaDataCoordinator(DataUpdateCoordinator[AlpacaData]):
    """Coordinator that polls the Alpaca Markets API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AlpacaAPIClient,
    ) -> None:
        """Initialize the coordinator."""
        update_interval_seconds = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        from datetime import timedelta

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> AlpacaData:
        """Fetch all data from Alpaca API."""
        try:
            account_raw, clock_raw, positions_raw, orders_raw = (
                await self._fetch_all()
            )
        except AlpacaAuthError as err:
            from homeassistant.exceptions import ConfigEntryAuthFailed

            raise ConfigEntryAuthFailed(
                f"Alpaca API authentication failed: {err}"
            ) from err
        except AlpacaConnectionError as err:
            raise UpdateFailed(f"Cannot connect to Alpaca API: {err}") from err
        except AlpacaError as err:
            raise UpdateFailed(f"Alpaca API error: {err}") from err

        return AlpacaData(
            account=_parse_account(account_raw),
            clock=_parse_clock(clock_raw),
            positions=_parse_positions(positions_raw),
            orders=_parse_orders(orders_raw),
            last_updated=dt_util.now(),
        )

    async def _fetch_all(
        self,
    ) -> tuple[
        dict[str, Any],
        dict[str, Any],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        """Fetch account, clock, positions and open orders concurrently."""
        import asyncio

        account_task = asyncio.create_task(self.client.get_account())
        clock_task = asyncio.create_task(self.client.get_clock())
        positions_task = asyncio.create_task(self.client.get_positions())
        orders_task = asyncio.create_task(self.client.get_orders(status="open"))

        account_raw = await account_task
        clock_raw = await clock_task
        positions_raw = await positions_task
        orders_raw = await orders_task

        return account_raw, clock_raw, positions_raw, orders_raw
