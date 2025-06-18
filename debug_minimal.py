#!/usr/bin/env python3

"""
Minimal debug to identify the data flow problem
"""

import pandas as pd
from datetime import datetime

# Test the specific problem: why DataFrame only has 2 columns
print("DEBUGGING CSV COLUMN ISSUE")
print("=" * 50)

# First, create a mock step_results to see if DataFrame creation works
test_step_results = {
    'timestamp': datetime(2024, 1, 1, 8, 0),
    'converged': True,
    'total_load_kw': 150.5,
    'total_losses_kw': 5.2,
    'total_bdwpt_kw': 25.0,
    'bdwpt_charging_kw': 30.0,
    'bdwpt_discharging_kw': 5.0,
    'voltage_bus_632': 1.02,
    'voltage_bus_633': 1.01,
    'voltage_bus_634': 0.99,
    'bdwpt_node_632_kw': 10.0,
    'bdwpt_node_633_kw': 15.0,
    'vehicles_G2V': 5,
    'vehicles_V2G': 2,
    'vehicles_idle': 3
}

print("1. Testing DataFrame creation with mock data:")
print(f"   Mock data keys: {list(test_step_results.keys())}")

# Create DataFrame from single record
df_test = pd.DataFrame([test_step_results])
print(f"   DataFrame shape: {df_test.shape}")
print(f"   DataFrame columns: {list(df_test.columns)}")

# Save test
test_file = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\debug_mock_test.csv"
df_test.to_csv(test_file, index=False)
print(f"   Saved mock test to: {test_file}")

# Now let's check what the actual simulation might be doing
print("\n2. Checking actual simulation components:")

try:
    from config import SimulationConfig
    config = SimulationConfig()
    print(f"   ✓ Config loaded")
    
    time_series = config.get_time_series()
    print(f"   ✓ Time series: {time_series['total_steps']} steps")
    
    # Check if there's a simplified/test mode
    import os
    if hasattr(config, 'test_mode') or hasattr(config, 'debug_mode'):
        print(f"   ⚠️  Test/debug mode detected!")
    
    # Check if the simulation is being overridden
    from cosimulation.simulation_engine import CoSimulationEngine
    print(f"   ✓ Simulation engine imported")
    
except Exception as e:
    print(f"   ✗ Error importing: {e}")

print("\n3. Analyzing existing results to find the issue:")

# Check if there's any pattern in the existing CSV
csv_path = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\Weekday_Peak_15pct\timeseries_data.csv"
if os.path.exists(csv_path):
    print(f"   Reading: {csv_path}")
    df_existing = pd.read_csv(csv_path)
    print(f"   Shape: {df_existing.shape}")
    print(f"   Columns: {list(df_existing.columns)}")
    print(f"   Data types: {df_existing.dtypes}")
    print(f"   Sample data:")
    print(df_existing)
    
    # Check if this looks like test data
    if df_existing.shape[0] <= 5 and 'load' in df_existing.columns:
        print(f"   ⚠️  This looks like TEST DATA, not real simulation results!")
        
        # Check for hardcoded values
        if len(df_existing['load'].unique()) <= 3:
            print(f"   ⚠️  Very few unique load values: {df_existing['load'].unique()}")
            print(f"   ⚠️  This suggests hardcoded test data!")

print("\nDEBUGGING COMPLETE")
