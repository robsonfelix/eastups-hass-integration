"""Button platform for EAST UPS integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import EastUPSCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class EastUPSButtonEntityDescription(ButtonEntityDescription):
    """Describes an EAST UPS button entity."""

    register: int
    value: int


# Control commands from official EA900 G4 Modbus Protocol (function code 0x06)
BUTTON_DESCRIPTIONS: Final[list[EastUPSButtonEntityDescription]] = [
    EastUPSButtonEntityDescription(
        key="clear_fault",
        name="Clear Fault",
        icon="mdi:alert-remove",
        entity_category=EntityCategory.DIAGNOSTIC,
        register=0x8000,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="clear_history",
        name="Clear History Log",
        icon="mdi:history",
        entity_category=EntityCategory.DIAGNOSTIC,
        register=0x8001,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="buzzer_mute",
        name="Mute Buzzer",
        icon="mdi:volume-off",
        register=0x8002,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="buzzer_unmute",
        name="Unmute Buzzer",
        icon="mdi:volume-high",
        register=0x8002,
        value=0,
    ),
    EastUPSButtonEntityDescription(
        key="battery_test_20s",
        name="Start Battery Test (20s)",
        icon="mdi:battery-sync",
        register=0x8006,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="battery_test_maintenance",
        name="Battery Maintenance Test",
        icon="mdi:battery-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        register=0x8006,
        value=2,
    ),
    EastUPSButtonEntityDescription(
        key="stop_battery_test",
        name="Stop Battery Test",
        icon="mdi:stop",
        register=0x8007,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="switch_to_bypass",
        name="Switch to Bypass",
        icon="mdi:swap-horizontal",
        entity_category=EntityCategory.CONFIG,
        register=0x8003,
        value=1,
    ),
    EastUPSButtonEntityDescription(
        key="switch_to_inverter",
        name="Switch to Inverter",
        icon="mdi:swap-horizontal-bold",
        entity_category=EntityCategory.CONFIG,
        register=0x8004,
        value=1,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EAST UPS buttons from a config entry."""
    coordinator: EastUPSCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[EastUPSButton] = [
        EastUPSButton(
            coordinator=coordinator,
            entry=entry,
            description=description,
        )
        for description in BUTTON_DESCRIPTIONS
    ]

    async_add_entities(entities)


class EastUPSButton(ButtonEntity):
    """Representation of an EAST UPS button."""

    entity_description: EastUPSButtonEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EastUPSCoordinator,
        entry: ConfigEntry,
        description: EastUPSButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        # Get serial number for device identification if available
        serial = coordinator.data.get("serial_number") if coordinator.data else None
        device_id = serial if serial else entry.entry_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=f"EAST UPS {coordinator.model}",
            manufacturer=MANUFACTURER,
            model=coordinator.model,
            serial_number=serial,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        desc = self.entity_description
        _LOGGER.info(
            "Sending command %s to register 0x%04X with value %d",
            desc.key,
            desc.register,
            desc.value,
        )
        await self._coordinator.async_write_register(desc.register, desc.value)
