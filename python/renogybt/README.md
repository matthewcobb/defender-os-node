# renogybt

A simplified, modular, and efficient library for communicating with Renogy solar charge controllers and batteries via Bluetooth.

## Overview

This library is a lightweight alternative to the original `renogybt` module, with a focus on:

- Simplified API with modern Python features (async/await, type hints)
- Better separation of concerns between components
- Enhanced reliability with improved connection management
- Same high-level functionality as the original library

The library is designed to work reliably on Raspberry Pi (including Pi 5) and efficiently manages connections to multiple Renogy BT devices.

## Key Components

### Connection Management

The `BleConnection` class handles all low-level Bluetooth operations:
- Device discovery
- Connection management with automatic retries
- Robust service discovery
- Reliable write operations with error handling

### Device Base Class

The `Device` class provides core functionality for all Renogy devices:
- Modbus protocol implementation (read/write operations)
- Register section polling with customizable intervals
- Data parsing framework
- Connection maintenance during polling

### Device Manager

The `DeviceManager` class simplifies working with multiple devices:
- Sequential connection to prevent BLE stack issues
- Sequential polling start to avoid overwhelming the BLE interface
- Centralized data and error handling
- Clean lifecycle management

### Device Implementations

Device-specific classes extend the base `Device` class with specialized functionality:

#### RoverDevice
For Renogy Rover/Wanderer/Adventurer solar charge controllers:
- Access to solar panel, battery, and load metrics
- Support for controlling load output
- Temperature monitoring

#### BatteryDevice
For Renogy LFP (Lithium) batteries:
- Individual cell voltage monitoring
- Battery temperature monitoring
- Charge/discharge status
- Capacity and state-of-charge tracking

## Comparison with Original renogybt

| Feature | renogybt | Original renogybt |
|---------|----------------|-------------------|
| Architecture | Modular (connection, device, manager) | Mixed concerns |
| API Style | Modern async/await | Callback-driven |
| Type Hints | Comprehensive | None |
| Error Handling | More robust | Basic |
| Connection Recovery | Enhanced | Basic |
| Memory Usage | Lower | Higher |
| Code Simplicity | Cleaner, more maintainable | More complex |

## Usage Example

### Solar Controller

```python
import asyncio
from renogybt import DeviceManager
from renogybt import RoverDevice

# Create device and manager
manager = DeviceManager()
rover = RoverDevice(
    mac_address="XX:XX:XX:XX:XX:XX",  # Your device MAC
    name="MySolarController"
)

# Register callbacks
async def on_data(device_key, device, data):
    print(f"Solar data: {device.get_summary()}")

manager.add_data_handler(on_data)
await manager.add_device("rover1", rover)

# Connect and start polling
await manager.connect_all_devices()
await manager.start_polling()
```

### Battery

```python
import asyncio
from renogybt import DeviceManager
from renogybt import BatteryDevice

# Create device and manager
manager = DeviceManager()
battery = BatteryDevice(
    mac_address="XX:XX:XX:XX:XX:XX",  # Your device MAC
    name="MyBattery"
)

# Register callbacks
async def on_data(device_key, device, data):
    print(f"Battery: {device.get_summary()}")
    cell_voltages = device.get_cell_voltages()
    print(f"Cell voltage difference: {data.get('cell_voltage_diff')}V")

manager.add_data_handler(on_data)
await manager.add_device("battery1", battery)

# Connect and start polling
await manager.connect_all_devices()
await manager.start_polling()
```

## Implementation Notes

1. The library automatically:
   - Waits for all devices to connect before polling
   - Manages connection failures and retries
   - Handles disconnections and reconnects during polling
   - Processes data responses from devices

2. Connection reliability is improved through:
   - Sequential device connection
   - Sequential polling starts
   - Proper connection lock management
   - Intelligent retry logic

3. BLE operations are optimized for:
   - Raspberry Pi compatibility
   - Prevention of BLE stack overflow
   - Service discovery robustness