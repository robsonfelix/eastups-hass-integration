"""DataUpdateCoordinator for EAST UPS integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BAUDRATE,
    CONF_MODEL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DOMAIN,
    MODEL_EA900_G4,
    MODEL_REGISTER_MAP,
    EastUPSSensorEntityDescription,
)

_LOGGER = logging.getLogger(__name__)


class EastUPSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching data from EAST UPS via Modbus."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._port = entry.data[CONF_SERIAL_PORT]
        self._baudrate = entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
        self._slave = entry.data.get(CONF_SLAVE, DEFAULT_SLAVE)
        self._model = entry.data.get(CONF_MODEL, MODEL_EA900_G4)
        self._client: AsyncModbusSerialClient | None = None
        self._lock = asyncio.Lock()

        # Get the sensor definitions for this model
        self._sensors = MODEL_REGISTER_MAP.get(self._model, MODEL_REGISTER_MAP[MODEL_EA900_G4])

        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def model(self) -> str:
        """Return the UPS model."""
        return self._model

    @property
    def sensors(self) -> dict[str, EastUPSSensorEntityDescription]:
        """Return the sensor definitions for this model."""
        return self._sensors

    async def _async_connect(self) -> bool:
        """Connect to the Modbus device."""
        if self._client is not None and self._client.connected:
            return True

        try:
            self._client = AsyncModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=3,
            )
            connected = await self._client.connect()
            if connected:
                _LOGGER.debug("Connected to Modbus device at %s", self._port)
            return connected
        except Exception as err:
            _LOGGER.error("Failed to connect to Modbus device: %s", err)
            self._client = None
            return False

    async def _async_disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        if self._client is not None:
            self._client.close()
            self._client = None

    async def _async_read_register(
        self,
        address: int,
        count: int = 1,
        input_type: str = "input",
    ) -> list[int] | None:
        """Read registers from the Modbus device."""
        if self._client is None or not self._client.connected:
            return None

        try:
            if input_type == "holding":
                response = await self._client.read_holding_registers(
                    address=address,
                    count=count,
                    device_id=self._slave,
                )
            else:
                response = await self._client.read_input_registers(
                    address=address,
                    count=count,
                    device_id=self._slave,
                )

            if response.isError():
                _LOGGER.warning(
                    "Error reading %s register %d: %s",
                    input_type,
                    address,
                    response,
                )
                return None

            _LOGGER.debug(
                "Read %s register %d: %s",
                input_type,
                address,
                response.registers,
            )

            return response.registers
        except ModbusException as err:
            _LOGGER.debug("Modbus exception reading register %d: %s", address, err)
            return None

    def _decode_string(self, registers: list[int]) -> str:
        """Decode ASCII string from registers."""
        chars = []
        for reg in registers:
            high_byte = (reg >> 8) & 0xFF
            low_byte = reg & 0xFF
            if high_byte != 0:
                chars.append(chr(high_byte))
            if low_byte != 0:
                chars.append(chr(low_byte))
        return "".join(chars).strip()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the UPS."""
        async with self._lock:
            if not await self._async_connect():
                raise UpdateFailed("Failed to connect to UPS")

            data: dict[str, Any] = {}

            for key, sensor_desc in self._sensors.items():
                if sensor_desc.register is None:
                    continue

                reg = sensor_desc.register
                registers = await self._async_read_register(
                    address=reg.address,
                    count=reg.count,
                    input_type=reg.input_type,
                )

                # Small delay between register reads to prevent UPS communication issues
                await asyncio.sleep(0.1)

                if registers is None:
                    data[key] = None
                    continue

                # Handle different data types
                if reg.data_type == "string":
                    value = self._decode_string(registers)
                elif reg.data_type == "int32" and len(registers) >= 2:
                    # Combine two 16-bit registers into 32-bit value
                    value = (registers[0] << 16) | registers[1]
                    value = value * reg.scale
                else:
                    # Standard 16-bit value
                    raw_value = registers[0]
                    # Handle signed values if needed
                    if raw_value > 32767:
                        raw_value = raw_value - 65536
                    value = raw_value * reg.scale

                # Apply value mapping if defined (for status codes)
                if sensor_desc.value_map and not isinstance(value, str):
                    int_value = int(value)
                    value = sensor_desc.value_map.get(int_value, f"Unknown ({int_value})")

                data[key] = value

            return data

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close connection."""
        await self._async_disconnect()
