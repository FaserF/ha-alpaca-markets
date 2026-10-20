"""Binary sensor platform for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import AlpacaData, AlpacaDataCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AlpacaBinarySensorDescription(BinarySensorEntityDescription):
    """Describes an Alpaca Markets binary sensor."""

    value_fn: Callable[[AlpacaData], bool]


BINARY_SENSORS: tuple[AlpacaBinarySensorDescription, ...] = (
    AlpacaBinarySensorDescription(
        key="market_open",
        translation_key="market_open",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.clock.is_open,
    ),
    AlpacaBinarySensorDescription(
        key="trading_blocked",
        translation_key="trading_blocked",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.account.trading_blocked,
    ),
    AlpacaBinarySensorDescription(
        key="account_blocked",
        translation_key="account_blocked",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.account.account_blocked,
        entity_registry_enabled_default=False,
    ),
    AlpacaBinarySensorDescription(
        key="account_restricted",
        translation_key="account_restricted",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.account.account_restricted,
    ),
    AlpacaBinarySensorDescription(
        key="pattern_day_trader",
        translation_key="pattern_day_trader",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.account.pattern_day_trader,
        entity_registry_enabled_default=False,
    ),
    AlpacaBinarySensorDescription(
        key="trade_suspended",
        translation_key="trade_suspended",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.account.trade_suspended_by_user,
        entity_registry_enabled_default=False,
    ),
    AlpacaBinarySensorDescription(
        key="shorting_enabled",
        translation_key="shorting_enabled",
        device_class=None,
        value_fn=lambda d: d.account.shorting_enabled,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Alpaca Markets binary sensor entities."""
    coordinator: AlpacaDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        AlpacaMarketsBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class AlpacaMarketsBinarySensor(
    CoordinatorEntity[AlpacaDataCoordinator], BinarySensorEntity
):
    """Binary sensor entity for Alpaca Markets."""

    entity_description: AlpacaBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AlpacaDataCoordinator,
        entry: ConfigEntry,
        description: AlpacaBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Alpaca Markets",
            model=entry.data.get("trading_mode", "paper").title() + " Trading",
            configuration_url="https://app.alpaca.markets/",
        )

    @property
    def is_on(self) -> bool | None:
        """Return binary sensor state."""
        if self.coordinator.data is None:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception:
            _LOGGER.debug(
                "Error reading binary sensor %s",
                self.entity_description.key,
                exc_info=True,
            )
            return None

    @property
    def available(self) -> bool:
        """Return True if data is available."""
        return super().available and self.coordinator.data is not None
