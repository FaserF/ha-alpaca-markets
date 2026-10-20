"""The Alpaca Markets integration.

Provides Home Assistant integration with Alpaca Markets trading platform:
- Account monitoring (portfolio value, cash, buying power, P&L)
- Market status (open/closed, next open/close times)
- Position tracking (open positions, unrealized P&L)
- Order management (open orders count, place/cancel orders)
- Services for order placement and position management
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api.client import AlpacaAPIClient
from .api.exceptions import AlpacaAuthError, AlpacaConnectionError, AlpacaError
from .const import (
    CONF_API_KEY_ID,
    CONF_API_SECRET_KEY,
    CONF_TRADING_MODE,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_TRADING_MODE,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AlpacaDataCoordinator
from .services import register_services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Alpaca Markets integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alpaca Markets from a config entry."""
    session = async_get_clientsession(hass)
    client = AlpacaAPIClient(
        api_key_id=entry.data[CONF_API_KEY_ID],
        api_secret_key=entry.data[CONF_API_SECRET_KEY],
        trading_mode=entry.data.get(CONF_TRADING_MODE, DEFAULT_TRADING_MODE),
        session=session,
    )

    # Validate credentials immediately
    try:
        await client.get_account()
    except AlpacaAuthError as err:
        raise ConfigEntryAuthFailed(
            f"Invalid Alpaca API credentials: {err}"
        ) from err
    except AlpacaConnectionError as err:
        raise ConfigEntryNotReady(
            f"Cannot connect to Alpaca API: {err}"
        ) from err
    except AlpacaError as err:
        raise ConfigEntryNotReady(f"Alpaca API error during setup: {err}") from err

    coordinator = AlpacaDataCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_CLIENT: client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration on options update."""
    await hass.config_entries.async_reload(entry.entry_id)
