"""Config flow for EAST UPS integration."""
from __future__ import annotations

import glob
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

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
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)


def get_serial_ports() -> list[str]:
    """Get list of available serial ports."""
    ports = []

    # Common serial port patterns
    patterns = [
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
        "/dev/serial/by-id/*",
        "/dev/ttyS*",
    ]

    for pattern in patterns:
        ports.extend(glob.glob(pattern))

    # Remove duplicates and sort
    return sorted(set(ports))


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    port = data[CONF_SERIAL_PORT]
    baudrate = data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
    slave = data.get(CONF_SLAVE, DEFAULT_SLAVE)

    def _test_connection() -> dict[str, Any]:
        """Test connection to the UPS."""
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=3,
        )

        try:
            if not client.connect():
                raise CannotConnect("Failed to connect to serial port")

            # Try to read a known register (input voltage at address 0)
            response = client.read_input_registers(address=0, count=1, device_id=slave)

            if response.isError():
                raise CannotConnect(f"Modbus error: {response}")

            # Read serial number for title
            serial_response = client.read_holding_registers(address=76, count=7, device_id=slave)
            serial = ""
            if not serial_response.isError():
                chars = []
                for reg in serial_response.registers:
                    high_byte = (reg >> 8) & 0xFF
                    low_byte = reg & 0xFF
                    if high_byte != 0:
                        chars.append(chr(high_byte))
                    if low_byte != 0:
                        chars.append(chr(low_byte))
                serial = "".join(chars).strip()

            return {"title": f"EAST UPS ({serial})" if serial else "EAST UPS"}

        except ModbusException as err:
            raise CannotConnect(f"Modbus exception: {err}") from err
        finally:
            client.close()

    return await hass.async_add_executor_job(_test_connection)


class EastUPSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EAST UPS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Get available serial ports
        serial_ports = await self.hass.async_add_executor_job(get_serial_ports)

        if not serial_ports:
            serial_ports = ["/dev/ttyUSB0"]  # Default fallback

        if user_input is not None:
            try:
                info = await validate_connection(self.hass, user_input)
            except CannotConnect as err:
                _LOGGER.error("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured with same serial port
                await self.async_set_unique_id(user_input[CONF_SERIAL_PORT])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        # Build schema with available serial ports
        data_schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL_PORT): vol.In(serial_ports),
                vol.Required(CONF_MODEL, default=MODEL_EA900_G4): vol.In(SUPPORTED_MODELS),
                vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.In(
                    [2400, 4800, 9600, 19200, 38400, 57600, 115200]
                ),
                vol.Optional(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=247)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=300)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
