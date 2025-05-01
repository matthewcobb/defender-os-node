import logging
import math

class LipoModel:
    def __init__(self, device_data):
        self.dcdc = device_data['rng_ctrl']
        self.batt = device_data['rng_batt']
        self.data = {}
        # Battery characteristics
        self.charge_efficiency = 0.9  # Typical LiPo charging efficiency
        self.temperature_factor = 1.0  # Default temperature factor

    def estimate_lipo_charging_time_cccv(self):
        # Use available properties from BatteryClient
        current_voltage = self.batt.get('voltage', 0)
        remaining_charge = self.batt.get('remaining_charge', 0)
        total_capacity = self.batt.get('capacity', 0)

        # Use available properties from RoverClient
        battery_current = self.dcdc.get('battery_current', 0)  # May be negative when discharging
        charging_status = self.dcdc.get('charging_status', 'deactivated')

        # If not charging, return appropriate message
        if charging_status == 'deactivated' or battery_current <= 0:
            return 'Not charging'

        # These should be configurable based on battery type
        target_voltage_cc = 14.4  # Constant current phase target voltage
        max_charge_voltage = 14.6  # Maximum charging voltage
        charging_current = abs(battery_current)  # Use actual charging current
        taper_current_threshold = 0.05 * total_capacity  # C/20 is typical end-of-charge

        # If already fully charged
        if current_voltage >= max_charge_voltage:
            return '0hrs'

        # Calculate remaining capacity to charge in Ah
        remaining_capacity_to_charge = total_capacity - remaining_charge

        # Adjust for charging efficiency
        adjusted_capacity = remaining_capacity_to_charge / self.charge_efficiency

        # Calculate time for CC phase (constant current)
        if current_voltage < target_voltage_cc:
            # Estimate capacity to charge during CC phase
            cc_phase_ratio = (target_voltage_cc - current_voltage) / (max_charge_voltage - current_voltage)
            cc_phase_capacity = adjusted_capacity * cc_phase_ratio
            time_cc = cc_phase_capacity / charging_current
        else:
            time_cc = 0  # Already in CV phase

        # Calculate time for CV phase
        # Using exponential decay model for CV phase
        if current_voltage < max_charge_voltage:
            # Remaining capacity for CV phase
            cv_phase_capacity = adjusted_capacity - (time_cc * charging_current)

            # Time constant for exponential decay (should be calibrated)
            tau = 2.0  # hours

            # Calculate CV phase time based on remaining capacity
            if cv_phase_capacity > 0:
                # Estimate CV phase time based on current battery voltage position
                cv_progress = 0
                if current_voltage > target_voltage_cc:
                    cv_progress = (current_voltage - target_voltage_cc) / (max_charge_voltage - target_voltage_cc)

                # Use logarithmic model for current decay
                time_cv = tau * math.log(charging_current / taper_current_threshold) * (1 - cv_progress)
            else:
                time_cv = 0
        else:
            time_cv = 0

        # Apply temperature correction if available
        # Check if temperature sensors exist in battery data
        has_temp = False
        avg_temp = 25  # Default room temperature

        # Check for temperature sensors in battery
        for i in range(4):  # Battery client has up to 4 temperature sensors
            temp_key = f'temperature_{i}'
            if temp_key in self.batt:
                has_temp = True
                avg_temp = float(self.batt[temp_key])
                break

        # If no battery temp, check controller temp
        if not has_temp and 'controller_temperature' in self.dcdc:
            has_temp = True
            avg_temp = float(self.dcdc['controller_temperature'])

        # Apply temperature correction
        if has_temp:
            # Temperature correction: charging slows at lower temperatures
            if avg_temp < 20:  # Below room temperature
                self.temperature_factor = 1 + (20 - avg_temp) * 0.03  # 3% slower per degree below 20°C
            else:
                self.temperature_factor = 1.0

            time_cc *= self.temperature_factor
            time_cv *= self.temperature_factor

        # Total time is the sum of both phases
        total_time = time_cc + time_cv

        return self.format_time(total_time)

    def estimate_lipo_discharging_time(self):
        # Use available properties from BatteryClient
        remaining_charge = self.batt.get('remaining_charge', 0)
        total_capacity = self.batt.get('capacity', 0)
        current_voltage = self.batt.get('voltage', 0)

        # Use available properties from RoverClient
        battery_current = self.dcdc.get('battery_current', 0)

        # Discharge happens when current is negative in the DC-DC controller
        discharge_rate = abs(battery_current) if battery_current < 0 else 0

        min_voltage = 10.0  # Minimum safe voltage

        # If no discharge is happening
        if discharge_rate <= 0:
            return 'Infinity'  # No consumption

        # If battery is already at or below minimum voltage
        if current_voltage <= min_voltage:
            return 'Already below min voltage'

        # Calculate usable capacity - use depth of discharge limits
        max_dod = 0.85  # Maximum depth of discharge for LiPo (~85%)
        usable_capacity = remaining_charge * max_dod

        # Apply Peukert's law to account for rate of discharge
        peukert_constant = 1.05  # LiPo typically 1.05-1.15 (lower is better)
        effective_capacity = usable_capacity * math.pow(total_capacity/discharge_rate, peukert_constant-1)

        # Check for temperature data and apply correction
        has_temp = False
        avg_temp = 25  # Default room temperature

        # Check for temperature sensors in battery
        for i in range(4):  # Battery client has up to 4 temperature sensors
            temp_key = f'temperature_{i}'
            if temp_key in self.batt:
                has_temp = True
                avg_temp = float(self.batt[temp_key])
                break

        # If no battery temp, check controller temp
        if not has_temp and 'controller_temperature' in self.dcdc:
            has_temp = True
            avg_temp = float(self.dcdc['controller_temperature'])

        # Apply temperature correction
        if has_temp and avg_temp < 20:
            # LiPo capacity is reduced at lower temperatures
            temp_factor = 1 - (20 - avg_temp) * 0.01  # 1% less capacity per degree below 20°C
            effective_capacity *= temp_factor

        # Calculate time left until battery reaches minimum safe level
        time_left_hours = effective_capacity / discharge_rate

        # Account for voltage curve - discharge accelerates at the end
        if current_voltage < 12.0:  # In the steeper part of discharge curve
            time_left_hours *= 0.8  # Reduce estimated time by 20%

        return self.format_time(time_left_hours)

    def format_time(self, hours):
        if hours < 0:
            return "0hrs"

        # Calculate hours and minutes
        hours_part = int(hours)
        minutes_part = int((hours - hours_part) * 60)

        # Build the formatted string
        formatted_time = f"{hours_part}hrs"
        if minutes_part > 0:
            formatted_time += f" {minutes_part}mins"

        return formatted_time

    def calculate(self):
        """Calculate derived metrics from raw device data"""
        try:
            # Fields to return to app
            self.data['time_remaining_to_charge'] = self.estimate_lipo_charging_time_cccv()
            self.data['time_remaining_to_empty'] = self.estimate_lipo_discharging_time()
            self.data['pv_power'] = self.dcdc.get('pv_power', 0)
            self.data['load_power'] = self.dcdc.get('load_power', 0)
            self.data['remaining_charge'] = self.batt.get('remaining_charge', 0)
            self.data['capacity'] = self.batt.get('capacity', 0)

            # Add fields with both naming conventions for compatibility
            self.data['battery_voltage'] = self.dcdc.get('battery_voltage', 0)
            self.data['battery_current'] = self.dcdc.get('battery_current', 0)
            self.data['battery_percentage'] = self.dcdc.get('battery_percentage', 0)
            self.data['charging_status'] = self.dcdc.get('charging_status', 'unknown')

            # Add cell count and sensor count for Vue app
            self.data['cell_count'] = self.batt.get('cell_count', 0)
            self.data['sensor_count'] = self.batt.get('sensor_count', 0)

            # Add device identifiers
            self.data['model'] = self.batt.get('model', 'Unknown')
            self.data['device_id'] = self.batt.get('device_id', 0)

            # Add all cell voltage and temperature values dynamically
            # Cell voltages: cell_voltage_0, cell_voltage_1, etc.
            for i in range(self.batt.get('cell_count', 0)):
                cell_key = f'cell_voltage_{i}'
                if cell_key in self.batt:
                    self.data[cell_key] = self.batt[cell_key]

            # Temperature sensors: temperature_0, temperature_1, etc.
            for i in range(self.batt.get('sensor_count', 0)):
                temp_key = f'temperature_{i}'
                if temp_key in self.batt:
                    self.data[temp_key] = self.batt[temp_key]

            # Additional solar data fields that might be needed
            self.data['pv_voltage'] = self.dcdc.get('pv_voltage', 0)
            self.data['pv_current'] = self.dcdc.get('pv_current', 0)
            self.data['controller_temperature'] = self.dcdc.get('controller_temperature', 0)
            self.data['power_generation_today'] = self.dcdc.get('power_generation_today', 0)
            self.data['power_generation_total'] = self.dcdc.get('power_generation_total', 0)
            self.data['max_charging_power_today'] = self.dcdc.get('max_charging_power_today', 0)

            # Log for debugging
            logging.debug(f"⚡ DCDC {self.dcdc}")
            logging.debug(f"⚡ BATT {self.batt}")

            return self.data
        except Exception as e:
            logging.error(f"🔴 Error in LipoModel calculate: {e}")
            return {'error': str(e)}