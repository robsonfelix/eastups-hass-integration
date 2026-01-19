"""Sensor platform for EAST UPS integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    EastUPSSensorEntityDescription,
)
from .coordinator import EastUPSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EAST UPS sensors from a config entry."""
    coordinator: EastUPSCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[EastUPSSensor] = []

    for key, description in coordinator.sensors.items():
        if description.register is not None:
            entities.append(
                EastUPSSensor(
                    coordinator=coordinator,
                    entry=entry,
                    description=description,
                    sensor_key=key,
                )
            )

    async_add_entities(entities)


class EastUPSSensor(CoordinatorEntity[EastUPSCoordinator], SensorEntity):
    """Representation of an EAST UPS sensor."""

    entity_description: EastUPSSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EastUPSCoordinator,
        entry: ConfigEntry,
        description: EastUPSSensorEntityDescription,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._sensor_key = sensor_key
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"

        # Get serial number for device identification if available
        serial = coordinator.data.get("serial_number") if coordinator.data else None
        device_id = serial if serial else entry.entry_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"EAST UPS {coordinator.model}",
            manufacturer=MANUFACTURER,
            model=coordinator.model,
            serial_number=serial,
            sw_version=coordinator.data.get("software_version") if coordinator.data else None,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(self._sensor_key)

        # Round numeric values for cleaner display
        if isinstance(value, float):
            # Determine precision based on the value
            if abs(value) >= 100:
                return round(value, 1)
            elif abs(value) >= 10:
                return round(value, 2)
            else:
                return round(value, 2)

        return value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
