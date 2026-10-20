"""Button platform for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.client import AlpacaAPIClient
from .api.exceptions import AlpacaError
from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AlpacaButtonDescription(ButtonEntityDescription):
    """Describes an Alpaca Markets button."""

    press_fn: Callable[[AlpacaAPIClient], Coroutine[Any, Any, None]]
    confirm_key: str | None = None


BUTTONS: tuple[AlpacaButtonDescription, ...] = (
    AlpacaButtonDescription(
        key="cancel_all_orders",
        translation_key="cancel_all_orders",
        press_fn=lambda client: client.cancel_all_orders(),
    ),
    AlpacaButtonDescription(
        key="close_all_positions",
        translation_key="close_all_positions",
        press_fn=lambda client: client.close_all_positions(cancel_orders=True),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Alpaca Markets button entities."""
    client: AlpacaAPIClient = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    async_add_entities(
        AlpacaMarketsButton(client, entry, description) for description in BUTTONS
    )


class AlpacaMarketsButton(ButtonEntity):
    """Button entity for Alpaca Markets actions."""

    entity_description: AlpacaButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        client: AlpacaAPIClient,
        entry: ConfigEntry,
        description: AlpacaButtonDescription,
    ) -> None:
        """Initialize the button."""
        self.entity_description = description
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Alpaca Markets",
            model=entry.data.get("trading_mode", "paper").title() + " Trading",
            configuration_url="https://app.alpaca.markets/",
        )

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            await self.entity_description.press_fn(self._client)
        except AlpacaError as err:
            _LOGGER.error(
                "Failed to execute button action %s: %s",
                self.entity_description.key,
                err,
            )
            raise
