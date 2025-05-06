"""
Simplified LipoModel for calculating battery metrics and time estimates
"""

import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class LipoModel:
    """
    Simplified model for calculating derived LiPo battery metrics
    including time to charge and discharge estimates
    """

    def __init__(self):
        """Initialize the LipoModel"""
        # Battery characteristics
        self.charge_efficiency = 0.9  # Typical LiPo charging efficiency
        self.max_depth_of_discharge = 0.95  # Maximum safe DoD for LiPo batteries

    def calculate(self, dcdc_data: Dict[str, Any], battery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived metrics from raw device data

        Args:
            dcdc_data: Data from the DCDC controller
            battery_data: Data from the Battery

        Returns:
            dict: Combined data with calculated metrics
        """
        if not dcdc_data or not battery_data:
            return {'error': 'Insufficient data'}

        try:
            # Create combined data structure
            combined = self._combine_device_data(dcdc_data, battery_data)

            # Add time estimates
            combined['time_remaining_to_charge'] = self._estimate_charging_time(combined)
            combined['time_remaining_to_empty'] = self._estimate_discharging_time(combined)

            return combined

        except Exception as e:
            log.error(f"❌ Error in LipoModel calculation: {e}")
            return {'error': f'Calculation error: {str(e)}'}

    def _combine_device_data(self, dcdc_data: Dict[str, Any], battery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine data from both devices into a single data structure
        """
        combined = {}

        # Add DCDC data
        combined['pv_power'] = dcdc_data.get('pv_power', 0)
        combined['pv_current'] = dcdc_data.get('pv_current', 0)
        combined['load_power'] = dcdc_data.get('load_power', 0)
        combined['load_current'] = dcdc_data.get('load_current', 0)
        combined['charger_status'] = dcdc_data.get('charging_status', 'unknown')
        combined['power_generation_today'] = dcdc_data.get('power_generation_today', 0)

        # Add battery data
        combined['battery_voltage'] = battery_data.get('voltage', 0)
        combined['battery_current'] = battery_data.get('current', 0)
        combined['battery_status'] = battery_data.get('status', 'unknown')
        combined['battery_percentage'] = battery_data.get('remaining_charge', 0)
        combined['battery_capacity'] = battery_data.get('capacity', 0)
        combined['battery_power'] = battery_data.get('power', 0)
        combined['cell_count'] = battery_data.get('cell_count', 0)
        combined['sensor_count'] = battery_data.get('sensor_count', 0)

        # Add calculated battery metrics
        combined['min_cell_voltage'] = battery_data.get('min_cell_voltage', 0)
        combined['max_cell_voltage'] = battery_data.get('max_cell_voltage', 0)
        combined['cell_voltage_diff'] = battery_data.get('cell_voltage_diff', 0)
        combined['min_temperature'] = battery_data.get('min_temperature', 0)
        combined['max_temperature'] = battery_data.get('max_temperature', 0)

        # Add all cell voltage values
        for i in range(battery_data.get('cell_count', 0)):
            cell_key = f'cell_voltage_{i}'
            if cell_key in battery_data:
                combined[cell_key] = battery_data[cell_key]

        # Add all temperature sensor values
        for i in range(battery_data.get('sensor_count', 0)):
            temp_key = f'temperature_{i}'
            if temp_key in battery_data:
                combined[temp_key] = battery_data[temp_key]

        return combined

    def _estimate_charging_time(self, data: Dict[str, Any]) -> str:
        """
        Estimate time to fully charge the battery

        Args:
            data: Combined device data

        Returns:
            str: Formatted time string
        """
        # Default response if not charging
        if data.get('battery_status') != "charging":
            return 'Not charging'

        # Get required values
        battery_capacity = data.get('battery_capacity', 0)  # Total capacity in Ah
        battery_percentage = data.get('battery_percentage', 0)  # Current charge percentage (0-100)
        battery_current = data.get('battery_current', 0)
        charging_rate = abs(battery_current)  # Charging current in Amps

        if charging_rate <= 0 or battery_capacity <= 0:
            return 'Already charged'

        # Calculate remaining capacity needed to charge in Ah
        remaining_capacity_ah = battery_capacity * (100 - battery_percentage) / 100

        # Apply charging efficiency factor
        adjusted_remaining = remaining_capacity_ah / self.charge_efficiency

        # Apply temperature correction if available
        temperature_factor = self._get_temperature_factor(data)
        adjusted_remaining = adjusted_remaining * temperature_factor

        # Calculate hours to charge and format (capacity in Ah / current in A = time in hours)
        hours = adjusted_remaining / charging_rate
        return self._format_time(hours)

    def _estimate_discharging_time(self, data: Dict[str, Any]) -> str:
        """
        Estimate time until battery is empty

        Args:
            data: Combined device data

        Returns:
            str: Formatted time string
        """
        # Check if battery is discharging based on battery_status
        if data.get('battery_status') != "discharging":
            return 'Infinity'  # Not discharging

        # Get required values
        battery_capacity = data.get('battery_capacity', 0)  # Total capacity in Ah
        battery_percentage = data.get('battery_percentage', 0)  # Current charge percentage (0-100)
        battery_current = data.get('battery_current', 0)
        discharge_rate = abs(battery_current)  # Discharge current in Amps

        if discharge_rate <= 0 or battery_percentage <= 0 or battery_capacity <= 0:
            return '0hrs'

        # Calculate remaining capacity in Ah
        remaining_capacity_ah = (battery_capacity * battery_percentage) / 100

        # Only use max_depth_of_discharge of capacity as usable
        usable_capacity_ah = remaining_capacity_ah * self.max_depth_of_discharge

        # Apply temperature correction
        temperature_factor = self._get_temperature_factor(data)
        usable_capacity_ah = usable_capacity_ah * temperature_factor

        # Calculate hours to discharge and format (capacity in Ah / current in A = time in hours)
        hours = usable_capacity_ah / discharge_rate
        return self._format_time(hours)

    def _get_temperature_factor(self, data: Dict[str, Any]) -> float:
        """
        Calculate temperature correction factor
        Lower temperatures reduce effective battery capacity

        Args:
            data: Combined device data

        Returns:
            float: Temperature correction factor
        """
        # Default temperature (room temperature)
        avg_temp = 25

        # Try to get battery temperature
        if data.get('min_temperature') is not None and data.get('max_temperature') is not None:
            avg_temp = (data.get('min_temperature', avg_temp) + data.get('max_temperature', avg_temp)) / 2

        # Apply temperature correction
        # LiPo capacity is reduced at lower temperatures
        if avg_temp < 20:
            # 1% less capacity per degree below 20°C
            return 1 - (20 - avg_temp) * 0.01

        return 1.0  # No correction at normal temperatures

    def _format_time(self, hours: float) -> str:
        """
        Format time in hours to readable string

        Args:
            hours: Time in hours

        Returns:
            str: Formatted time string
        """
        if hours <= 0:
            return "0hrs"

        # Calculate hours and minutes
        hours_part = int(hours)
        minutes_part = int((hours - hours_part) * 60)

        # Build the formatted string
        formatted_time = f"{hours_part}hrs"
        if minutes_part > 0:
            formatted_time += f" {minutes_part}mins"

        return formatted_time