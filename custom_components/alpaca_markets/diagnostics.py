"""Diagnostics support for Alpaca Markets."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY_ID, CONF_TRADING_MODE, DATA_COORDINATOR, DOMAIN
from .coordinator import AlpacaDataCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: AlpacaDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    data = coordinator.data

    diag: dict[str, Any] = {
        "integration": {
            "domain": DOMAIN,
            "version": "1.0.0-dev0",
            "trading_mode": entry.data.get(CONF_TRADING_MODE, "paper"),
            "api_key_id": f"***{entry.data.get(CONF_API_KEY_ID, '')[-4:]}",
            "entry_id": entry.entry_id,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_updated": str(coordinator.last_update_success),
        },
    }

    if data is not None:
        diag["account"] = {
            "status": data.account.status,
            "currency": data.account.currency,
            "trading_blocked": data.account.trading_blocked,
            "account_blocked": data.account.account_blocked,
            "account_restricted": data.account.account_restricted,
            "pattern_day_trader": data.account.pattern_day_trader,
            "shorting_enabled": data.account.shorting_enabled,
            "multiplier": data.account.multiplier,
        }
        diag["market"] = {
            "is_open": data.clock.is_open,
            "next_open": data.clock.next_open,
            "next_close": data.clock.next_close,
        }
        diag["positions"] = {
            "count": data.positions.count,
        }
        diag["orders"] = {
            "open_count": data.orders.open_count,
        }

    return diag
