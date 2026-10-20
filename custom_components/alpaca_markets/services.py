"""Services for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .api.client import AlpacaAPIClient
from .api.exceptions import AlpacaError
from .const import (
    DATA_CLIENT,
    DOMAIN,
    ORDER_SIDE_BUY,
    ORDER_SIDE_SELL,
    ORDER_TYPE_LIMIT,
    ORDER_TYPE_MARKET,
    ORDER_TYPE_STOP,
    ORDER_TYPE_STOP_LIMIT,
    SERVICE_CANCEL_ORDER,
    SERVICE_CLOSE_POSITION,
    SERVICE_PLACE_ORDER,
    TIME_IN_FORCE_DAY,
    TIME_IN_FORCE_FOK,
    TIME_IN_FORCE_GTC,
    TIME_IN_FORCE_IOC,
)

_LOGGER = logging.getLogger(__name__)

PLACE_ORDER_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("symbol"): cv.string,
        vol.Required("side"): vol.In([ORDER_SIDE_BUY, ORDER_SIDE_SELL]),
        vol.Required("order_type"): vol.In(
            [ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, ORDER_TYPE_STOP, ORDER_TYPE_STOP_LIMIT]
        ),
        vol.Required("time_in_force"): vol.In(
            [TIME_IN_FORCE_DAY, TIME_IN_FORCE_GTC, TIME_IN_FORCE_IOC, TIME_IN_FORCE_FOK]
        ),
        vol.Optional("qty"): vol.Coerce(float),
        vol.Optional("notional"): vol.Coerce(float),
        vol.Optional("limit_price"): vol.Coerce(float),
        vol.Optional("stop_price"): vol.Coerce(float),
    }
)

CANCEL_ORDER_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("order_id"): cv.string,
    }
)

CLOSE_POSITION_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("symbol"): cv.string,
        vol.Optional("qty"): vol.Coerce(float),
        vol.Optional("percentage"): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
    }
)


def _get_client(hass: HomeAssistant, entry_id: str) -> AlpacaAPIClient:
    """Retrieve the API client for the given config entry ID."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry_id)
    if not entry_data:
        msg = f"No Alpaca Markets entry found with ID '{entry_id}'"
        raise ValueError(msg)
    return entry_data[DATA_CLIENT]


def register_services(hass: HomeAssistant) -> None:
    """Register Alpaca Markets services."""

    async def _handle_place_order(call: ServiceCall) -> None:
        """Handle the place_order service call."""
        client = _get_client(hass, call.data["entry_id"])
        try:
            order = await client.place_order(
                symbol=call.data["symbol"],
                qty=call.data.get("qty"),
                side=call.data["side"],
                order_type=call.data["order_type"],
                time_in_force=call.data["time_in_force"],
                limit_price=call.data.get("limit_price"),
                stop_price=call.data.get("stop_price"),
                notional=call.data.get("notional"),
            )
            _LOGGER.info(
                "Order placed: %s %s %s (id: %s)",
                call.data["side"],
                call.data.get("qty", call.data.get("notional")),
                call.data["symbol"],
                order.get("id"),
            )
        except AlpacaError as err:
            _LOGGER.error("Failed to place order: %s", err)
            raise

    async def _handle_cancel_order(call: ServiceCall) -> None:
        """Handle the cancel_order service call."""
        client = _get_client(hass, call.data["entry_id"])
        try:
            await client.cancel_order(call.data["order_id"])
            _LOGGER.info("Order %s cancelled", call.data["order_id"])
        except AlpacaError as err:
            _LOGGER.error("Failed to cancel order %s: %s", call.data["order_id"], err)
            raise

    async def _handle_close_position(call: ServiceCall) -> None:
        """Handle the close_position service call."""
        client = _get_client(hass, call.data["entry_id"])
        try:
            await client.close_position(
                symbol=call.data["symbol"],
                qty=call.data.get("qty"),
                percentage=call.data.get("percentage"),
            )
            _LOGGER.info("Position closed: %s", call.data["symbol"])
        except AlpacaError as err:
            _LOGGER.error(
                "Failed to close position %s: %s", call.data["symbol"], err
            )
            raise

    if not hass.services.has_service(DOMAIN, SERVICE_PLACE_ORDER):
        hass.services.async_register(
            DOMAIN, SERVICE_PLACE_ORDER, _handle_place_order, schema=PLACE_ORDER_SCHEMA
        )
    if not hass.services.has_service(DOMAIN, SERVICE_CANCEL_ORDER):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CANCEL_ORDER,
            _handle_cancel_order,
            schema=CANCEL_ORDER_SCHEMA,
        )
    if not hass.services.has_service(DOMAIN, SERVICE_CLOSE_POSITION):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CLOSE_POSITION,
            _handle_close_position,
            schema=CLOSE_POSITION_SCHEMA,
        )
