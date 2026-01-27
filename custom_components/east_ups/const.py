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


class SystemMode(IntEnum):
    """System mode codes from register 71."""
    FAULT = 0
    POWER_ON = 1
    STANDBY = 2
    BYPASS = 3
    GRID = 4
    BATTERY = 5
    BATTERY_CHECK = 6
    FAULT_2 = 7  # Second fault mode in doc
    FREQUENCY_CONVERT = 8
    ECO = 9
    SHUTDOWN = 10
    TEST = 11


class BatteryStatus(IntEnum):
    """Battery status codes from Status Word register 70, bits 5-7."""
    DISCONNECTED = 0
    STANDBY = 1
    BOOST_CHARGING = 2
    FLOAT_CHARGING = 3
    DISCHARGING = 4


class RectifierStatus(IntEnum):
    """Rectifier status from Status Word register 70, bits 1-2."""
    OFF = 0
    SOFTSTART = 1
    PFC_MODE = 2
    BATTERY_MODE = 3


class InverterStatus(IntEnum):
    """Inverter status from Status Word register 70, bits 3-4."""
    OFF = 0
    SOFTSTART = 1
    NORMAL = 2
    STANDBY = 3


class BypassStatus(IntEnum):
    """Bypass status from Status Word register 70, bits 8-9."""
    NO_BYPASS = 0
    NORMAL = 1


class LoadOnStatus(IntEnum):
    """Load on status from Status Word register 70, bits 10-11."""
    NONE = 0
    LOAD_ON_BYPASS = 1
    LOAD_ON_INVERTER = 2
    LOAD_ON_OTHER = 3


SYSTEM_MODE_TEXT: Final = {
    SystemMode.FAULT: "Fault",
    SystemMode.POWER_ON: "Power On",
    SystemMode.STANDBY: "Standby",
    SystemMode.BYPASS: "Bypass",
    SystemMode.GRID: "Grid",
    SystemMode.BATTERY: "Battery",
    SystemMode.BATTERY_CHECK: "Battery Check",
    SystemMode.FAULT_2: "Fault",
    SystemMode.FREQUENCY_CONVERT: "Frequency Convert",
    SystemMode.ECO: "ECO",
    SystemMode.SHUTDOWN: "Shutdown",
    SystemMode.TEST: "Test",
}

BATTERY_STATUS_TEXT: Final = {
    BatteryStatus.DISCONNECTED: "Disconnected",
    BatteryStatus.STANDBY: "Standby",
    BatteryStatus.BOOST_CHARGING: "Boost Charging",
    BatteryStatus.FLOAT_CHARGING: "Float Charging",
    BatteryStatus.DISCHARGING: "Discharging",
}

RECTIFIER_STATUS_TEXT: Final = {
    RectifierStatus.OFF: "Off",
    RectifierStatus.SOFTSTART: "Soft Start",
    RectifierStatus.PFC_MODE: "PFC Mode",
    RectifierStatus.BATTERY_MODE: "Battery Mode",
}

INVERTER_STATUS_TEXT: Final = {
    InverterStatus.OFF: "Off",
    InverterStatus.SOFTSTART: "Soft Start",
    InverterStatus.NORMAL: "Normal",
    InverterStatus.STANDBY: "Standby",
}

BYPASS_STATUS_TEXT: Final = {
    BypassStatus.NO_BYPASS: "No Bypass",
    BypassStatus.NORMAL: "Normal",
}

LOAD_ON_STATUS_TEXT: Final = {
    LoadOnStatus.NONE: "None",
    LoadOnStatus.LOAD_ON_BYPASS: "Load on Bypass",
    LoadOnStatus.LOAD_ON_INVERTER: "Load on Inverter",
    LoadOnStatus.LOAD_ON_OTHER: "Load on Other",
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
# Based on official EAST EA900 G4 6-20k Modbus Protocol document (Sep 2020)
# ============================================================================

EA900_G4_INPUT_REGISTERS: Final[dict[str, EastUPSSensorEntityDescription]] = {
    # === BYPASS ===
    "bypass_voltage": EastUPSSensorEntityDescription(
        key="bypass_voltage",
        name="Bypass Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=0, scale=0.1),  # Doc: reg 0
    ),
    "bypass_current": EastUPSSensorEntityDescription(
        key="bypass_current",
        name="Bypass Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=3, scale=0.1),  # Doc: reg 3
    ),
    "bypass_frequency": EastUPSSensorEntityDescription(
        key="bypass_frequency",
        name="Bypass Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=6, scale=0.1),  # Doc: reg 6
    ),
    "bypass_power_factor": EastUPSSensorEntityDescription(
        key="bypass_power_factor",
        name="Bypass Power Factor",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=9, scale=0.01),  # Doc: reg 9, coef 0.01
    ),
    # === INPUT (Grid) ===
    "input_voltage": EastUPSSensorEntityDescription(
        key="input_voltage",
        name="Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=12, scale=0.1),  # Doc: reg 12
    ),
    "input_current": EastUPSSensorEntityDescription(
        key="input_current",
        name="Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=15, scale=0.1),  # Doc: reg 15
    ),
    "input_frequency": EastUPSSensorEntityDescription(
        key="input_frequency",
        name="Input Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=18, scale=0.1),  # Doc: reg 18
    ),
    "input_power_factor": EastUPSSensorEntityDescription(
        key="input_power_factor",
        name="Input Power Factor",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=21, scale=0.01),  # Doc: reg 21, coef 0.01
    ),
    # === OUTPUT ===
    "output_voltage": EastUPSSensorEntityDescription(
        key="output_voltage",
        name="Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=24, scale=0.1),  # Doc: reg 24
    ),
    "output_current": EastUPSSensorEntityDescription(
        key="output_current",
        name="Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=27, scale=0.1),  # Doc: reg 27
    ),
    "output_frequency": EastUPSSensorEntityDescription(
        key="output_frequency",
        name="Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=30, scale=0.1),  # Doc: reg 30
    ),
    "output_power_factor": EastUPSSensorEntityDescription(
        key="output_power_factor",
        name="Output Power Factor",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=33, scale=0.01),  # Reverse-engineered (Reserved in doc)
    ),
    "output_apparent_power": EastUPSSensorEntityDescription(
        key="output_apparent_power",
        name="Output Apparent Power",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=36, scale=100),  # Doc: reg 36, 0.1 kVA = 100 VA
    ),
    "output_active_power": EastUPSSensorEntityDescription(
        key="output_active_power",
        name="Output Active Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=39, scale=100),  # Doc: reg 39, 0.1 kW = 100 W
    ),
    "output_reactive_power": EastUPSSensorEntityDescription(
        key="output_reactive_power",
        name="Output Reactive Power",
        native_unit_of_measurement="var",
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=42, scale=100),  # Doc: reg 42, 0.1 kVAR = 100 VAR
    ),
    "load_percentage": EastUPSSensorEntityDescription(
        key="load_percentage",
        name="Load",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=45, scale=0.1),  # Doc: reg 45
    ),
    # === BATTERY ===
    "battery_voltage": EastUPSSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=49, scale=0.1),  # Doc: reg 49
    ),
    "battery_current": EastUPSSensorEntityDescription(
        key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=51, scale=0.1),  # Doc: reg 51
    ),
    "battery_temperature": EastUPSSensorEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=53, scale=0.1),  # Doc: reg 53
    ),
    "battery_remaining_time": EastUPSSensorEntityDescription(
        key="battery_remaining_time",
        name="Battery Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=54, scale=1),  # Doc: reg 54
    ),
    "battery_remaining_capacity": EastUPSSensorEntityDescription(
        key="battery_remaining_capacity",
        name="Battery Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        register=EastUPSRegisterDefinition(address=55, scale=0.1),  # Doc: reg 55
    ),
    # === DIAGNOSTIC: TEMPERATURES & CURRENTS ===
    "inverter_current": EastUPSSensorEntityDescription(
        key="inverter_current",
        name="Inverter Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=56, scale=0.1),  # Doc: reg 56
    ),
    "rectifier_temperature": EastUPSSensorEntityDescription(
        key="rectifier_temperature",
        name="Rectifier Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=57, scale=0.1),  # Doc: reg 57
    ),
    "inverter_temperature": EastUPSSensorEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=58, scale=0.1),  # Doc: reg 58
    ),
    "ups_run_days": EastUPSSensorEntityDescription(
        key="ups_run_days",
        name="UPS Run Days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=59, scale=1),  # Doc: reg 59
    ),
    # === SOFTWARE VERSION ===
    "software_version": EastUPSSensorEntityDescription(
        key="software_version",
        name="Software Version",
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=67, scale=1, data_type="string", count=3),  # Doc: reg 67-69
    ),
    # === STATUS WORD (register 70) - parsed as bitfield in coordinator ===
    "status_word": EastUPSSensorEntityDescription(
        key="status_word",
        name="Status Word",
        native_unit_of_measurement=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=70, scale=1, data_type="uint16"),  # Doc: reg 70
    ),
    # === SYSTEM MODE ===
    "system_mode": EastUPSSensorEntityDescription(
        key="system_mode",
        name="System Mode",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        register=EastUPSRegisterDefinition(address=71, scale=1),  # Doc: reg 71
        value_map=SYSTEM_MODE_TEXT,
    ),
    # === DERIVED STATUS FROM STATUS WORD (bits 5-7) ===
    "battery_status": EastUPSSensorEntityDescription(
        key="battery_status",
        name="Battery Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        register=None,  # Derived from status_word in coordinator
        value_map=BATTERY_STATUS_TEXT,
    ),
    "rectifier_status": EastUPSSensorEntityDescription(
        key="rectifier_status",
        name="Rectifier Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=None,  # Derived from status_word in coordinator
        value_map=RECTIFIER_STATUS_TEXT,
    ),
    "inverter_status": EastUPSSensorEntityDescription(
        key="inverter_status",
        name="Inverter Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=None,  # Derived from status_word in coordinator
        value_map=INVERTER_STATUS_TEXT,
    ),
    "bypass_status": EastUPSSensorEntityDescription(
        key="bypass_status",
        name="Bypass Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=None,  # Derived from status_word in coordinator
        value_map=BYPASS_STATUS_TEXT,
    ),
    "load_on_status": EastUPSSensorEntityDescription(
        key="load_on_status",
        name="Load On Status",
        native_unit_of_measurement=None,
        device_class=SensorDeviceClass.ENUM,
        register=None,  # Derived from status_word in coordinator
        value_map=LOAD_ON_STATUS_TEXT,
    ),
}

EA900_G4_HOLDING_REGISTERS: Final[dict[str, EastUPSSensorEntityDescription]] = {
    # === DIAGNOSTIC: Device info (from reverse engineering, not in official doc) ===
    # Note: These are read-only diagnostic values, not actual config settings
    "rated_power": EastUPSSensorEntityDescription(
        key="rated_power",
        name="Rated Power",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=15, scale=1, input_type="holding"),
    ),
    "battery_count": EastUPSSensorEntityDescription(
        key="battery_count",
        name="Battery Count",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=5, scale=1, input_type="holding"),
    ),
    "cell_float_voltage": EastUPSSensorEntityDescription(
        key="cell_float_voltage",
        name="Cell Float Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=7, scale=0.01, input_type="holding"),
    ),
    "cell_boost_voltage": EastUPSSensorEntityDescription(
        key="cell_boost_voltage",
        name="Cell Boost Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=8, scale=0.01, input_type="holding"),
    ),
    "battery_maintenance_cycle": EastUPSSensorEntityDescription(
        key="battery_maintenance_cycle",
        name="Battery Maintenance Cycle",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=26, scale=1, input_type="holding"),
    ),
    "running_time": EastUPSSensorEntityDescription(
        key="running_time",
        name="Running Time",
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        register=EastUPSRegisterDefinition(address=27, scale=7, input_type="holding"),  # Weeks * 7 = days
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
