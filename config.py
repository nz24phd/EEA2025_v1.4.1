# config.py - Configuration parameters for BDWPT simulation

import os
import numpy as np
from datetime import datetime, timedelta

class SimulationConfig:
    """Central configuration for all simulation parameters"""
    
    def __init__(self):
        # Simulation parameters
        self.simulation_start = datetime(2024, 6, 1, 0, 0, 0)  # Start at midnight
        self.simulation_duration_hours = 24  # 24-hour simulation
        self.time_step_minutes = 1  # 1-minute resolution
        self.total_time_steps = self.simulation_duration_hours * 60 // self.time_step_minutes
        
        # Geographic parameters (Wellington, NZ)
        self.city_name = "Wellington"
        self.country = "New Zealand"
        self.timezone = "Pacific/Auckland"
        
        # Traffic model parameters
        self.traffic_params = {
            'total_vehicles': 10000,  # Total vehicles in simulated area
            'ev_penetration': 0.30,   # 30% of vehicles are EVs
            'peak_hours_morning': (7, 9),  # Morning peak
            'peak_hours_evening': (17, 19),  # Evening peak
            'average_trip_distance_km': 8.5,  # Average trip distance
            'trips_per_vehicle_per_day': 3.2,  # Average trips per vehicle
        }
        
        # EV and BDWPT parameters
        self.ev_params = {
            'battery_capacity_kwh': 60,  # Average EV battery capacity
            'initial_soc_mean': 0.7,     # Mean initial SoC
            'initial_soc_std': 0.15,     # Std deviation of initial SoC
            'energy_consumption_kwh_per_km': 0.18,  # Energy efficiency
            'min_soc_threshold': 0.2,    # Minimum SoC before forced charging
            'max_soc_threshold': 0.9,    # Maximum SoC limit
        }
        
        # BDWPT charging parameters
        self.bdwpt_params = {
            'charging_power_kw': 50,     # BDWPT charging power
            'discharging_power_kw': 30,  # BDWPT discharging power
            'efficiency': 0.92,          # Power transfer efficiency
            'coverage_ratio': 0.3,       # 30% of roads have BDWPT
        }
        
        # Control strategy parameters
        self.control_params = {
            # SoC thresholds
            'soc_force_charge': 0.3,     # Force G2V below this
            'soc_force_discharge': 0.8,  # Force V2G above this
            'soc_min_v2g': 0.5,         # Minimum SoC for V2G
            
            # Voltage thresholds (p.u.)
            'voltage_high_threshold': 1.05,
            'voltage_low_threshold': 0.95,
            'voltage_critical_high': 1.10,
            'voltage_critical_low': 0.90,
            
            # Tariff thresholds ($/kWh)
            'tariff_high': 0.35,
            'tariff_medium': 0.25,
            'tariff_low': 0.15,
        }
        
        # Power grid parameters (IEEE 13-bus)
        self.grid_params = {
            'base_voltage_kv': 4.16,     # IEEE 13-bus base voltage
            'base_power_mva': 5.0,       # Base power
            'frequency_hz': 50,          # NZ grid frequency
            'bdwpt_nodes': [6, 7, 8, 9, 10, 11, 12, 13],  # Nodes with BDWPT
        }
        
        # Time-of-use tariff structure (NZ typical)
        self.tariff_schedule = {
            'peak': {
                'hours': [(7, 11), (17, 21)],
                'rate': 0.35  # $/kWh
            },
            'shoulder': {
                'hours': [(11, 17), (21, 23)],
                'rate': 0.25  # $/kWh
            },
            'off_peak': {
                'hours': [(23, 7)],
                'rate': 0.15  # $/kWh
            }
        }
        
        # Scenario definitions
        self.scenarios = {
            'Weekday Peak': {
                'traffic_multiplier': 1.2,
                'load_profile': 'weekday',
            },
            'Weekend Peak': {
                'traffic_multiplier': 0.8,
                'load_profile': 'weekend',
            }
        }
        
        # Output directories
        self.output_dir = "output"
        self.results_dir = os.path.join(self.output_dir, "results")
        self.figures_dir = os.path.join(self.output_dir, "figures")
        self.data_dir = "data"
        
        # Create directories if they don't exist
        for directory in [self.output_dir, self.results_dir, self.figures_dir, self.data_dir]:
            os.makedirs(directory, exist_ok=True)
            
    def get_tariff_at_hour(self, hour):
        """Get electricity tariff for a given hour"""
        for period, info in self.tariff_schedule.items():
            for start, end in info['hours']:
                if start <= hour < end or (start > end and (hour >= start or hour < end)):
                    return info['rate']
        return self.tariff_schedule['off_peak']['rate']  # Default
        
    def get_time_series(self):
        """Generate time series for simulation"""
        times = []
        current_time = self.simulation_start
        
        for _ in range(self.total_time_steps):
            times.append(current_time)
            current_time += timedelta(minutes=self.time_step_minutes)
            
        return times
        
    def get_load_profile(self, profile_type='weekday'):
        """Generate typical load profile for Wellington"""
        hours = np.arange(24)
        
        if profile_type == 'weekday':
            # Typical weekday load profile (normalized)
            base_load = np.array([
                0.5, 0.45, 0.42, 0.40, 0.42, 0.48, 0.58, 0.75,  # 0-7
                0.85, 0.88, 0.87, 0.85, 0.83, 0.82, 0.84, 0.86,  # 8-15
                0.88, 0.95, 1.0, 0.98, 0.92, 0.80, 0.65, 0.55   # 16-23
            ])
        else:  # weekend
            # Typical weekend load profile (normalized)
            base_load = np.array([
                0.55, 0.50, 0.48, 0.45, 0.45, 0.47, 0.52, 0.60,  # 0-7
                0.70, 0.78, 0.82, 0.85, 0.86, 0.85, 0.83, 0.82,  # 8-15
                0.84, 0.88, 0.92, 0.90, 0.85, 0.75, 0.65, 0.58   # 16-23
            ])
            
        # Interpolate to minute resolution
        minute_load = np.interp(
            np.arange(0, 24, self.time_step_minutes/60),
            hours,
            base_load
        )
        
        return minute_load