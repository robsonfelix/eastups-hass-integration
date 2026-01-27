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
    BATTERY_STATUS_TEXT,
    RECTIFIER_STATUS_TEXT,
    INVERTER_STATUS_TEXT,
    BYPASS_STATUS_TEXT,
    LOAD_ON_STATUS_TEXT,
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

    def _parse_status_word(self, status_word: int) -> dict[str, str]:
        """Parse the status word bitfield from register 70.

        Bit layout (per official EA900 G4 doc):
        - bits 0-1: Rectifier status (0: off, 1: softstart, 2: PFC mode, 3: battery mode)
        - bits 2-3: Inverter status (0: off, 1: softstart, 2: normal, 3: standby)
        - bits 4-6: Battery status (0: disconnect, 1: standby, 2: boosting, 3: floating, 4: discharge)
        - bits 7-8: Bypass status (0: no bypass, 1: normal)
        - bits 9-10: Load on status (0: none, 1: load on bypass, 2: load on inverter, 3: load on other)
        - bits 11-15: Reserved

        Note: Doc says bit1-bit2, bit3-bit4, etc. but uses 1-based indexing.
        In 0-based indexing: bits 0-1, 2-3, 4-6, 7-8, 9-10
        """
        # Extract bit fields (0-based indexing)
        rectifier_status = status_word & 0x03  # bits 0-1
        inverter_status = (status_word >> 2) & 0x03  # bits 2-3
        battery_status = (status_word >> 4) & 0x07  # bits 4-6
        bypass_status = (status_word >> 7) & 0x03  # bits 7-8
        load_on_status = (status_word >> 9) & 0x03  # bits 9-10

        return {
            "rectifier_status": RECTIFIER_STATUS_TEXT.get(rectifier_status, f"Unknown ({rectifier_status})"),
            "inverter_status": INVERTER_STATUS_TEXT.get(inverter_status, f"Unknown ({inverter_status})"),
            "battery_status": BATTERY_STATUS_TEXT.get(battery_status, f"Unknown ({battery_status})"),
            "bypass_status": BYPASS_STATUS_TEXT.get(bypass_status, f"Unknown ({bypass_status})"),
            "load_on_status": LOAD_ON_STATUS_TEXT.get(load_on_status, f"Unknown ({load_on_status})"),
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the UPS."""
        async with self._lock:
            if not await self._async_connect():
                raise UpdateFailed("Failed to connect to UPS")

            data: dict[str, Any] = {}

            for key, sensor_desc in self._sensors.items():
                if sensor_desc.register is None:
                    # Derived sensors (battery_status, etc.) - skip for now
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
                elif reg.data_type == "uint16":
                    # Unsigned 16-bit value (e.g., status word)
                    value = registers[0]
                else:
                    # Standard signed 16-bit value
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

            # Parse status word to derive battery/rectifier/inverter/bypass/load status
            if "status_word" in data and data["status_word"] is not None:
                status_values = self._parse_status_word(int(data["status_word"]))
                data.update(status_values)
                _LOGGER.debug("Parsed status word %d: %s", data["status_word"], status_values)

            _LOGGER.debug("Coordinator data: %s", data)
            return data

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and close connection."""
        await self._async_disconnect()
