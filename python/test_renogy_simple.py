#!/usr/bin/env python3
"""
Test script for the simplified renogybt library.
This provides a command-line interface to test connectivity to Renogy devices.
"""

import asyncio
import logging
import argparse
import json
from typing import Dict, Any

from renogybt import DeviceManager, RoverDevice, BatteryDevice
from config.settings import DCDC_CONFIG, BATTERY_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

class RenogyTester:
    """Test class for Renogy device connections"""

    def __init__(self, device_types=None):
        """Initialize the tester with specific device types"""
        self.device_types = device_types or ['dcdc', 'battery']
        self.device_manager = DeviceManager()
        self.data = {}

    async def setup(self):
        """Set up the devices"""
        # Create and add devices
        if 'dcdc' in self.device_types:
            dcdc_device = RoverDevice(
                mac_address=DCDC_CONFIG['mac_addr'],
                name=DCDC_CONFIG['alias'],
                device_id=DCDC_CONFIG['device_id']
            )
            await self.device_manager.add_device('dcdc', dcdc_device)
            log.info(f"Added DCDC device: {DCDC_CONFIG['alias']}")

        if 'battery' in self.device_types:
            battery_device = BatteryDevice(
                mac_address=BATTERY_CONFIG['mac_addr'],
                name=BATTERY_CONFIG['alias'],
                device_id=BATTERY_CONFIG['device_id']
            )
            await self.device_manager.add_device('battery', battery_device)
            log.info(f"Added Battery device: {BATTERY_CONFIG['alias']}")

        # Register data handler
        self.device_manager.add_data_handler(self.on_device_data)
        self.device_manager.add_error_handler(self.on_device_error)

    async def run_test(self, duration=60):
        """Run the test for a specified duration"""
        try:
            # Connect devices
            log.info("Connecting to devices...")
            connected = await self.device_manager.connect_all_devices()

            if connected:
                log.info("✅ All devices connected successfully")
            else:
                log.warning("⚠️ Not all devices connected")

            # Start polling
            log.info("Starting device polling...")
            await self.device_manager.start_polling()

            # Wait for data collection
            log.info(f"Collecting data for {duration} seconds...")

            # Display periodic updates during the test
            for i in range(duration):
                if i > 0 and i % 10 == 0:
                    self.display_summary()
                await asyncio.sleep(1)

            # Final data display
            log.info("Test completed!")
            self.display_detailed_data()

        finally:
            # Cleanup
            log.info("Stopping all devices...")
            await self.device_manager.stop()

    async def on_device_data(self, device_key, device, data):
        """Handle device data updates"""
        self.data[device_key] = data.copy()
        log.debug(f"Received data from {device_key}")

    async def on_device_error(self, device_key, device, error):
        """Handle device errors"""
        log.error(f"Error from {device_key}: {error}")

    def display_summary(self):
        """Display a summary of the current device data"""
        if not self.data:
            log.info("No data available yet")
            return

        # Show DCDC data
        if 'dcdc' in self.data:
            dcdc = self.data['dcdc']
            log.info("⚡ DCDC Status:")
            log.info(f"  • PV Power: {dcdc.get('pv_power', 'N/A')}W")
            log.info(f"  • Battery: {dcdc.get('battery_voltage', 'N/A')}V, {dcdc.get('battery_current', 'N/A')}A")
            log.info(f"  • Charging: {dcdc.get('charging_status', 'N/A')}")

        # Show Battery data
        if 'battery' in self.data:
            batt = self.data['battery']
            log.info("🔋 Battery Status:")
            log.info(f"  • SOC: {batt.get('soc_percent', 'N/A')}%")
            log.info(f"  • Cells: {batt.get('cell_count', 'N/A')}, "
                    f"Min: {batt.get('min_cell_voltage', 'N/A')}V, "
                    f"Max: {batt.get('max_cell_voltage', 'N/A')}V, "
                    f"Diff: {batt.get('cell_voltage_diff', 'N/A')}V")

    def display_detailed_data(self):
        """Display detailed data from all devices"""
        if not self.data:
            log.info("No data available")
            return

        # Print full data for each device
        for device_key, data in self.data.items():
            log.info(f"\n📊 {device_key.upper()} DETAILED DATA:")
            # Format as pretty JSON
            formatted_data = json.dumps(data, indent=2, sort_keys=True)
            print(formatted_data)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test Renogy devices')
    parser.add_argument('-d', '--duration', type=int, default=60,
                        help='Test duration in seconds (default: 60)')
    parser.add_argument('--dcdc-only', action='store_true',
                        help='Test only the DCDC controller')
    parser.add_argument('--battery-only', action='store_true',
                        help='Test only the Battery')
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_args()

    # Determine which devices to test
    if args.dcdc_only:
        device_types = ['dcdc']
    elif args.battery_only:
        device_types = ['battery']
    else:
        device_types = ['dcdc', 'battery']

    # Create and run tester
    tester = RenogyTester(device_types)
    await tester.setup()
    await tester.run_test(args.duration)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        log.error(f"Error during test: {e}", exc_info=True)