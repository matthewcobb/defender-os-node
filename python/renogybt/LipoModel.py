import logging

class LipoModel:
    def __init__(self, dcdc, batt):
        self.dcdc = dcdc
        self.batt = batt
        self.data = {}
        # Parse the JSON strings and merge them into one dictionary

    def estimate_lipo_charging_time_cccv(self):
        current_voltage = self.batt['voltage']
        target_voltage_cc = 14.4
        constant_current = 20
        battery_total_capacity = self.batt['capacity']
        # taper_current_threshold = 2
        average_cv_factor = 0.5

        if current_voltage >= target_voltage_cc:
            return 0  # Already at or above target voltage for CC phase

        # Calculate time for CC phase
        cc_phase_capacity = (target_voltage_cc - current_voltage) * battery_total_capacity / target_voltage_cc
        time_cc = cc_phase_capacity / constant_current  # Time for CC phase in hours

        # Estimate time for CV phase (manufacturer suggests 7 hours total, so subtract CC phase time)
        # This is an approximation since we don't have the exact tapering profile
        time_cv = max(7 - time_cc, 0) * average_cv_factor  # Apply factor to adjust for actual tapering profile

        # Total time is the sum of both phases
        total_time = time_cc + time_cv

        # Add the result to the data dictionary
        return self.format_time(total_time) # Time left in hours until the battery is fully charged


    def estimate_lipo_discharging_time(self):
        current_capacity = self.batt['remaining_charge']
        discharge_rate = self.dcdc['battery_current']
        battery_total_capacity = self.batt['capacity']
        min_voltage = 10
        current_voltage = self.batt['voltage']

       # Calculate the remaining capacity that can be used before reaching the minimum voltage
        usable_capacity = (current_voltage - min_voltage) * battery_total_capacity / current_voltage

        # If the discharge rate is zero or usable capacity is already below zero, return 'Infinity' or 'Already below min voltage'
        if discharge_rate == 0:
            return 'Infinity'  # Can't estimate time if there's no consumption
        if usable_capacity <= 0:
            return 'Already below min voltage'

        # Calculate time left until the battery reaches the minimum voltage
        time_left_hours = usable_capacity / discharge_rate

        return self.format_time(time_left_hours)  # Time left in hours until the battery reaches min voltage

    def format_time(self, hours):
        # Calculate hours and minutes
        hours_part = int(hours)
        minutes_part = int((hours - hours_part) * 60)

        # Build the formatted string
        formatted_time = f"{hours_part}hrs"
        if minutes_part > 0:
            formatted_time += f" {minutes_part}mins"

        return formatted_time

    def calculate(self):
        # Fields to return to app
        self.data['time_remaining_to_charge'] = self.estimate_lipo_charging_time_cccv()
        self.data['time_remaining_to_empty'] = self.estimate_lipo_discharging_time()
        self.data['pv_power'] = self.dcdc['pv_power']
        self.data['load_power'] = self.dcdc['load_power']
        self.data['remaining_charge'] = self.batt['remaining_charge']
        print("---")
        logging.info(f"DCDC {self.dcdc}")
        print("---")
        logging.info(f"BATT {self.batt}")
        print("---")
        return self.data
