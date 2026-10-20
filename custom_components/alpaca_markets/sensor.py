"""Sensor platform for the Alpaca Markets integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import AlpacaData, AlpacaDataCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class AlpacaSensorDescription(SensorEntityDescription):
    """Describes an Alpaca Markets sensor."""

    value_fn: Callable[[AlpacaData], Any]
    available_fn: Callable[[AlpacaData], bool] = lambda _: True


ACCOUNT_SENSORS: tuple[AlpacaSensorDescription, ...] = (
    AlpacaSensorDescription(
        key="portfolio_value",
        translation_key="portfolio_value",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.portfolio_value, 2),
    ),
    AlpacaSensorDescription(
        key="cash",
        translation_key="cash",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.cash, 2),
    ),
    AlpacaSensorDescription(
        key="equity",
        translation_key="equity",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.equity, 2),
    ),
    AlpacaSensorDescription(
        key="last_equity",
        translation_key="last_equity",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.last_equity, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="buying_power",
        translation_key="buying_power",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.buying_power, 2),
    ),
    AlpacaSensorDescription(
        key="daytrading_buying_power",
        translation_key="daytrading_buying_power",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.daytrading_buying_power, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="long_market_value",
        translation_key="long_market_value",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.long_market_value, 2),
    ),
    AlpacaSensorDescription(
        key="short_market_value",
        translation_key="short_market_value",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.short_market_value, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="unrealized_pl",
        translation_key="unrealized_pl",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.unrealized_pl, 2),
    ),
    AlpacaSensorDescription(
        key="unrealized_plpc",
        translation_key="unrealized_plpc",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(d.account.unrealized_plpc * 100, 4),
    ),
    AlpacaSensorDescription(
        key="realized_pl",
        translation_key="realized_pl",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.realized_pl, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="initial_margin",
        translation_key="initial_margin",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.initial_margin, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="maintenance_margin",
        translation_key="maintenance_margin",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.account.maintenance_margin, 2),
        entity_registry_enabled_default=False,
    ),
    AlpacaSensorDescription(
        key="daytrade_count",
        translation_key="daytrade_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.account.daytrade_count,
    ),
    AlpacaSensorDescription(
        key="account_status",
        translation_key="account_status",
        value_fn=lambda d: d.account.status.lower(),
    ),
)

POSITION_SENSORS: tuple[AlpacaSensorDescription, ...] = (
    AlpacaSensorDescription(
        key="positions_count",
        translation_key="positions_count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.positions.count,
    ),
    AlpacaSensorDescription(
        key="positions_market_value",
        translation_key="positions_market_value",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.positions.total_market_value, 2),
    ),
    AlpacaSensorDescription(
        key="positions_unrealized_pl",
        translation_key="positions_unrealized_pl",
        native_unit_of_measurement=CURRENCY_DOLLAR,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda d: round(d.positions.total_unrealized_pl, 2),
    ),
)

ORDER_SENSORS: tuple[AlpacaSensorDescription, ...] = (
    AlpacaSensorDescription(
        key="open_orders",
        translation_key="open_orders",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.orders.open_count,
    ),
)

CLOCK_SENSORS: tuple[AlpacaSensorDescription, ...] = (
    AlpacaSensorDescription(
        key="next_market_open",
        translation_key="next_market_open",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: (
            dt_util.parse_datetime(d.clock.next_open) if d.clock.next_open else None
        ),
    ),
    AlpacaSensorDescription(
        key="next_market_close",
        translation_key="next_market_close",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: (
            dt_util.parse_datetime(d.clock.next_close) if d.clock.next_close else None
        ),
    ),
)

ALL_SENSORS = ACCOUNT_SENSORS + POSITION_SENSORS + ORDER_SENSORS + CLOCK_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Alpaca Markets sensor entities."""
    coordinator: AlpacaDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        AlpacaMarketsSensor(coordinator, entry, description)
        for description in ALL_SENSORS
    )


class AlpacaMarketsSensor(CoordinatorEntity[AlpacaDataCoordinator], SensorEntity):
    """Sensor entity for Alpaca Markets data."""

    entity_description: AlpacaSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AlpacaDataCoordinator,
        entry: ConfigEntry,
        description: AlpacaSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Alpaca Markets",
            model=entry.data.get("trading_mode", "paper").title() + " Trading",
            configuration_url="https://app.alpaca.markets/",
        )

    @property
    def native_value(self) -> Any:
        """Return sensor value."""
        if self.coordinator.data is None:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception:
            _LOGGER.debug(
                "Error reading sensor %s", self.entity_description.key, exc_info=True
            )
            return None

    @property
    def available(self) -> bool:
        """Return True if coordinator data is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.available_fn(self.coordinator.data)
        )
