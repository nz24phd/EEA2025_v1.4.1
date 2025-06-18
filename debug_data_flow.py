#!/usr/bin/env python3

import pandas as pd
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Analyzing existing simulation results...")

try:
    # 1. Check what's actually in the saved CSV file
    csv_file = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\Weekday_Peak_15pct\timeseries_data.csv"
    print(f"1. Reading existing CSV: {csv_file}")
    
    df = pd.read_csv(csv_file)
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Data types: {df.dtypes}")
    print(f"   First few rows:")
    print(df.head())
    
    # 2. Run a small test simulation to debug data flow
    print("\n2. Testing simulation data collection...")
    
    from config import SimulationConfig
    from traffic_model.data_loader import TrafficDataLoader
    from traffic_model.main_traffic import TrafficModel
    from power_grid_model.ieee_13_bus_model import IEEE13BusSystem
    from cosimulation.simulation_engine import CoSimulationEngine
    from cosimulation.scenarios import ScenarioManager
    
    config = SimulationConfig()
    data_loader = TrafficDataLoader(config.data_dir)
    traffic_model = TrafficModel(config, data_loader)
    power_grid = IEEE13BusSystem(config)
    power_grid.build_network()
    
    cosim_engine = CoSimulationEngine(config, traffic_model, power_grid)
    scenario_manager = ScenarioManager(config)
    
    # Set up for 15% BDWPT penetration
    traffic_model.set_bdwpt_penetration(15)
    
    # Test one time step in detail
    print("\n3. Testing one simulation step...")
    
    from datetime import datetime
    timestamp = datetime(2024, 1, 1, 8, 0)  # 8 AM
    
    # Calculate BDWPT powers
    bdwpt_powers = cosim_engine._calculate_bdwpt_powers(8)
    print(f"   BDWPT powers: {bdwpt_powers}")
    print(f"   Total BDWPT power: {sum(bdwpt_powers.values()):.2f} kW")
    
    # Update grid loads
    cosim_engine._update_grid_loads(8, "Weekday Peak", bdwpt_powers)
    
    # Solve power flow
    pf_results = power_grid.solve_power_flow()
    print(f"   Power flow results keys: {pf_results.keys()}")
    print(f"   Powers: {pf_results.get('powers', {})}")
    print(f"   Voltages sample: {dict(list(pf_results.get('voltages', {}).items())[:3])}")
    
    # Collect step results
    step_results = cosim_engine._collect_step_results(timestamp, pf_results, bdwpt_powers)
    print(f"\n4. Step results analysis:")
    print(f"   Keys: {sorted(step_results.keys())}")
    print(f"   Total load: {step_results.get('total_load_kw', 'MISSING')}")
    print(f"   Total BDWPT: {step_results.get('total_bdwpt_kw', 'MISSING')}")
    print(f"   BDWPT charging: {step_results.get('bdwpt_charging_kw', 'MISSING')}")
    print(f"   BDWPT discharging: {step_results.get('bdwpt_discharging_kw', 'MISSING')}")
    
    # Check for voltage data
    voltage_keys = [k for k in step_results.keys() if 'voltage' in k]
    print(f"   Voltage keys count: {len(voltage_keys)}")
    if voltage_keys:
        print(f"   Sample voltage keys: {voltage_keys[:3]}")
    
    # Check for BDWPT node data
    bdwpt_node_keys = [k for k in step_results.keys() if 'bdwpt_node' in k]
    print(f"   BDWPT node keys count: {len(bdwpt_node_keys)}")
    if bdwpt_node_keys:
        print(f"   Sample BDWPT node keys: {bdwpt_node_keys[:3]}")
    
    # Test DataFrame creation
    print(f"\n5. Testing DataFrame creation...")
    results_data = [step_results]  # Single step for testing
    
    df_test = pd.DataFrame(results_data)
    print(f"   Test DataFrame shape: {df_test.shape}")
    print(f"   Test DataFrame columns: {list(df_test.columns)}")
    
    # Show non-null columns
    non_null_cols = df_test.columns[df_test.notna().any()].tolist()
    print(f"   Non-null columns: {non_null_cols}")
    
    # Save test DataFrame
    test_file = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\debug_test_data.csv"
    df_test.to_csv(test_file, index=False)
    print(f"   Saved test data to: {test_file}")
    
except Exception as e:
    import traceback
    print(f"✗ Error: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
