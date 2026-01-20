"""Constants for the EAST UPS integration."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)

DOMAIN: Final = "east_ups"
MANUFACTURER: Final = "EAST Group / Intelbras"

# Default configuration
DEFAULT_PORT: Final = "/dev/ttyUSB0"
DEFAULT_BAUDRATE: Final = 9600
DEFAULT_SLAVE: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 30

# Configuration keys
CONF_SERIAL_PORT: Final = "serial_port"
CONF_BAUDRATE: Final = "baudrate"
CONF_SLAVE: Final = "slave"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MODEL: Final = "model"

# Supported models
MODEL_EA900_G4: Final = "EA900 G4"
MODEL_EA660_G4: Final = "EA660 G4"

SUPPORTED_MODELS: Final = [MODEL_EA900_G4, MODEL_EA660_G4]


class BatteryStatus(IntEnum):
    """Battery status codes."""
    IDLE = 0
    CHARGING = 1
    DISCHARGING = 2
    EQUALIZED_CHARGING = 3
    FLOAT_CHARGING = 4
    SLEEP = 5
    DISCONNECTED = 6


class PowerSupplyMode(IntEnum):
    """Power supply mode codes."""
    NO_POWER = 0
    MAINS = 1
    BATTERY = 2
    COMBINED = 3
    BYPASS = 4


BATTERY_STATUS_TEXT: Final = {
    BatteryStatus.IDLE: "Idle",
    BatteryStatus.CHARGING: "Charging",
    BatteryStatus.DISCHARGING: "Discharging",
    BatteryStatus.EQUALIZED_CHARGING: "Equalized Charging",
    BatteryStatus.FLOAT_CHARGING: "Float Charging",
    BatteryStatus.SLEEP: "Sleep",
    BatteryStatus.DISCONNECTED: "Disconnected",
}

POWER_SUPPLY_MODE_TEXT: Final = {
    PowerSupplyMode.NO_POWER: "No Power",
    PowerSupplyMode.MAINS: "Mains",
    PowerSupplyMode.BATTERY: "Battery",
    PowerSupplyMode.COMBINED: "Combined",
    PowerSupplyMode.BYPASS: "Bypass",
}


@dataclass(frozen=True)
class EastUPSRegisterDefinition:
    """Definition of a Modbus register."""
    address: int
    scale: float = 1.0
    input_type: str = "input"  # "input" or "holding"
    data_type: str = "int16"  # "int16", "uint16", "int32", "string"
    count: int = 1  # Number of registers (for strings or 32-bit values)


@dataclass(frozen=True, kw_only=True)
class EastUPSSensorEntityDescription(SensorEntityDescription):
    """Describes an EAST UPS sensor entity."""
    register: EastUPSRegisterDefinition | None = None
    value_map: dict | None = None  # For status code to text mapping


# ============================================================================
# EA900 G4 Register Map (Intelbras DNB 6kVA)
# Based on reverse engineering and comparison with upsSmartView app
# ============================================================================

EA900_G4_INPUT_REGISTERS: Final[dict[str, EastUPSSensorEntityDescription]] = {
    # === INPUT (Grid) ===
    "input_voltage": EastUPSSensorEntityDescription(
        key="input_voltage",
        name="Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=0, scale=0.1),
    ),
    "input_current": EastUPSSensorEntityDescription(
        key="input_current",
        name="Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=15, scale=0.1),
    ),
    "input_frequency": EastUPSSensorEntityDescription(
        key="input_frequency",
        name="Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=18, scale=0.1),
    ),
    "input_power_factor": EastUPSSensorEntityDescription(
        key="input_power_factor",
        name="Input Power Factor",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=21, scale=1),
    ),
    # === BYPASS ===
    "bypass_voltage": EastUPSSensorEntityDescription(
        key="bypass_voltage",
        name="Bypass Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=12, scale=0.1),
    ),
    "bypass_frequency": EastUPSSensorEntityDescription(
        key="bypass_frequency",
        name="Bypass Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=6, scale=0.1),
    ),
    # === OUTPUT ===
    "output_voltage": EastUPSSensorEntityDescription(
        key="output_voltage",
        name="Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=24, scale=0.1),
    ),
    "output_current": EastUPSSensorEntityDescription(
        key="output_current",
        name="Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=27, scale=0.1),
    ),
    "output_frequency": EastUPSSensorEntityDescription(
        key="output_frequency",
        name="Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=30, scale=0.1),
    ),
    "output_power_factor": EastUPSSensorEntityDescription(
        key="output_power_factor",
        name="Output Power Factor",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=33, scale=1),
    ),
    "output_apparent_power": EastUPSSensorEntityDescription(
        key="output_apparent_power",
        name="Output Apparent Power",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=36, scale=100),  # 0.1 kVA = 100 VA
    ),
    "output_active_power": EastUPSSensorEntityDescription(
        key="output_active_power",
        name="Output Active Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=39, scale=100),  # 0.1 kW = 100 W
    ),
    "load_percentage": EastUPSSensorEntityDescription(
        key="load_percentage",
        name="Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=45, scale=0.1),
    ),
    # === BATTERY ===
    "battery_charge": EastUPSSensorEntityDescription(
        key="battery_charge",
        name="Battery Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=9, scale=1),
    ),
    "battery_voltage": EastUPSSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=49, scale=0.1),
    ),
    "battery_current": EastUPSSensorEntityDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=51, scale=0.1),
    ),
    "battery_remaining_time": EastUPSSensorEntityDescription(
        key="battery_remaining_time",
        name="Battery Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=54, scale=1),
    ),
    "battery_remaining_capacity": EastUPSSensorEntityDescription(
        key="battery_remaining_capacity",
        name="Battery Remaining Capacity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=55, scale=0.1),
    ),
    # === DIAGNOSTIC: TEMPERATURES & CURRENTS ===
    "inverter_current": EastUPSSensorEntityDescription(
        key="inverter_current",
        name="Inverter Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=56, scale=0.1),
    ),
    "rectifier_temperature": EastUPSSensorEntityDescription(
        key="rectifier_temperature",
        name="Rectifier Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=57, scale=0.1),
    ),
    "inverter_temperature": EastUPSSensorEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=58, scale=0.1),
    ),
    "bus_temperature": EastUPSSensorEntityDescription(
        key="bus_temperature",
        name="Bus Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=59, scale=0.1),
    ),
    # === STATUS ===
    "battery_status": EastUPSSensorEntityDescription(
        key="battery_status",
        name="Battery Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        register=EastUPSRegisterDefinition(address=71, scale=1),
        value_map=BATTERY_STATUS_TEXT,
    ),
    # === DIAGNOSTIC INFO ===
    "software_version": EastUPSSensorEntityDescription(
        key="software_version",
        name="Software Version",
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=67, scale=1, data_type="string", count=3),
    ),
}

EA900_G4_HOLDING_REGISTERS: Final[dict[str, EastUPSSensorEntityDescription]] = {
    # === CONFIG: Device settings ===
    "rated_power": EastUPSSensorEntityDescription(
        key="rated_power",
        name="Rated Power",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.CONFIG,
        register=EastUPSRegisterDefinition(address=15, scale=1, input_type="holding"),
    ),
    "battery_count": EastUPSSensorEntityDescription(
        key="battery_count",
        name="Battery Count",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.CONFIG,
        register=EastUPSRegisterDefinition(address=5, scale=1, input_type="holding"),
    ),
    "cell_float_voltage": EastUPSSensorEntityDescription(
        key="cell_float_voltage",
        name="Cell Float Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.CONFIG,
        register=EastUPSRegisterDefinition(address=7, scale=0.01, input_type="holding"),
    ),
    "cell_boost_voltage": EastUPSSensorEntityDescription(
        key="cell_boost_voltage",
        name="Cell Boost Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.CONFIG,
        register=EastUPSRegisterDefinition(address=8, scale=0.01, input_type="holding"),
    ),
    "battery_maintenance_cycle": EastUPSSensorEntityDescription(
        key="battery_maintenance_cycle",
        name="Battery Maintenance Cycle",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.CONFIG,
        register=EastUPSRegisterDefinition(address=26, scale=1, input_type="holding"),
    ),
    "running_time": EastUPSSensorEntityDescription(
        key="running_time",
        name="Running Time",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        register=EastUPSRegisterDefinition(address=27, scale=7, input_type="holding"),  # weeks * 7 = days (updates weekly)
    ),
    # === SERIAL NUMBER (ASCII) ===
    "serial_number": EastUPSSensorEntityDescription(
        key="serial_number",
        name="Serial Number",
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=76, scale=1, input_type="holding", data_type="string", count=7),
    ),
}

# Combined register map for EA900 G4
EA900_G4_SENSORS: Final[dict[str, EastUPSSensorEntityDescription]] = {
    **EA900_G4_INPUT_REGISTERS,
    **EA900_G4_HOLDING_REGISTERS,
}

# Model to register map mapping
MODEL_REGISTER_MAP: Final = {
    MODEL_EA900_G4: EA900_G4_SENSORS,
    # MODEL_EA660_G4: EA660_G4_SENSORS,  # TODO: Add EA660 G4 support
}
