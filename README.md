# EAST UPS Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/robsonfelix/eastups-hass-integration.svg)](https://github.com/robsonfelix/eastups-hass-integration/releases)
[![License](https://img.shields.io/github/license/robsonfelix/eastups-hass-integration.svg)](LICENSE)

A Home Assistant custom integration for EAST Group UPS devices, including **Intelbras DNB series** (which are rebranded EAST UPS units).

## Supported Devices

| Model | Status | Notes |
|-------|--------|-------|
| **EA900 G4** (Intelbras DNB 6kVA) | ✅ Tested | Fully supported |
| EA660 G4 | 🔄 Planned | Similar protocol, may work |

## Features

- **Easy Setup**: Configure via Home Assistant UI (no YAML required)
- **All Sensors**: Input, output, bypass, battery, and temperature readings
- **Status Monitoring**: Battery status, load status with text descriptions
- **Device Info**: Serial number, software version, rated power
- **Efficient Polling**: Uses DataUpdateCoordinator for optimized communication

## Sensors

### Power Monitoring
- Input/Output/Bypass Voltage (V)
- Input/Output Current (A)
- Input/Output Frequency (Hz)
- Input/Output Power Factor
- Output Apparent Power (VA)
- Output Active Power (W)
- Load Percentage (%)

### Battery
- Battery Charge (%)
- Battery Voltage (V)
- Battery Current (A)
- Battery Status (Idle, Charging, Discharging, Float Charging, etc.)

### Temperatures
- Rectifier Temperature (°C)
- Inverter Temperature (°C)
- Bus Temperature (°C)

### Device Information
- Running Time (days)
- Serial Number
- Software Version
- Rated Power (VA)
- Cell Float/Boost Voltage (V)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add `https://github.com/robsonfelix/eastups-hass-integration` with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/robsonfelix/eastups-hass-integration/releases)
2. Extract and copy the `custom_components/east_ups` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "EAST UPS"
4. Select your serial port and configure:
   - **Serial Port**: The USB serial port (e.g., `/dev/ttyUSB0` or `/dev/serial/by-id/...`)
   - **Model**: Select your UPS model
   - **Baud Rate**: Usually 9600 (default)
   - **Slave Address**: Usually 1 (default)
   - **Scan Interval**: How often to poll (default: 30 seconds)

## Hardware Connection

The UPS connects via RS485/USB adapter. Common setup:

```
UPS RS485 Port → RS485-to-USB Adapter → Home Assistant Host
```

Typical serial port paths:
- `/dev/ttyUSB0`
- `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`

## Troubleshooting

### Cannot Connect
- Check the serial port path is correct
- Verify the USB adapter is connected and recognized (`ls /dev/ttyUSB*`)
- Ensure baud rate matches UPS settings (default: 9600)
- Check Modbus slave address (default: 1)

### Sensors Show Unknown/Unavailable
- Some sensors may not be available on all models
- Check Home Assistant logs for Modbus communication errors

### Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.east_ups: debug
```

## Development

Based on reverse engineering of the EAST EA900 G4 Modbus protocol, with reference to the EA660 G4 documentation.

### Register Map

The integration includes a detailed register map in `const.py` based on:
- EA660 G4 Modbus Communication Protocol V1.9
- Live testing with Intelbras DNB 6kVA (EA900 G4)
- Comparison with upsSmartView Windows application

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

If you have a different EAST/Intelbras UPS model and want to help add support, please open an issue with:
- Your UPS model name
- Screenshots from upsSmartView app (if available)
- Any Modbus register documentation you have

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- EAST Group for the EA660 G4 Modbus protocol documentation
- Home Assistant community for integration development guidance
