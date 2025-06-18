#!/usr/bin/env python3

import logging
import pandas as pd
from datetime import datetime, timedelta

# Set up logging to capture all debug info
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("FULL SIMULATION DATA FLOW DEBUG")
print("=" * 60)

try:
    # Import components
    from config import SimulationConfig
    from cosimulation.simulation_engine import CoSimulationEngine
    from cosimulation.scenarios import ScenarioManager
    
    print("✓ All imports successful")
    
    # Initialize config
    config = SimulationConfig()
    
    # Create simulation engine
    cosim_engine = CoSimulationEngine(config)
    
    # Test scenario
    scenario_manager = ScenarioManager(config)
    scenario = scenario_manager.get_scenario("Weekday Peak", 15)
    
    print(f"✓ Testing scenario: {scenario}")
    print(f"✓ BDWPT penetration: {scenario['bdwpt_penetration']}%")
    
    # Run just 3 time steps to debug data collection
    print("\n" + "=" * 40)
    print("RUNNING LIMITED SIMULATION (3 steps)")
    print("=" * 40)
    
    # Initialize simulation
    cosim_engine._initialize_simulation(scenario)
    print(f"✓ Initialized {len(cosim_engine.bdwpt_agents)} BDWPT agents")
    
    # Collect step-by-step results
    results_data = []
    start_time = datetime(2024, 1, 1, 8, 0)  # Start at 8 AM
    
    for step in range(3):
        timestamp = start_time + timedelta(minutes=step * config.time_step_minutes)
        hour = timestamp.hour
        print(f"\n--- STEP {step + 1}: {timestamp} ---")
        
        # Update traffic
        day_type = 'weekday'
        cosim_engine._update_traffic(timestamp, day_type)
        print(f"✓ Traffic updated for hour {hour}")
        
        # Calculate BDWPT powers
        bdwpt_powers = cosim_engine._calculate_bdwpt_powers(hour)
        print(f"✓ BDWPT powers: {bdwpt_powers}")
        print(f"  Total BDWPT power: {sum(bdwpt_powers.values()):.2f} kW")
        
        # Update grid loads
        load_profile_type = scenario['load_profile']
        cosim_engine._update_grid_loads(hour, load_profile_type, bdwpt_powers)
        print(f"✓ Grid loads updated")
        
        # Solve power flow
        pf_results = cosim_engine.power_grid.solve_power_flow()
        print(f"✓ Power flow solved: converged={pf_results['converged']}")
        print(f"  Total load: {pf_results['powers']['total_load']:.2f} kW")
        print(f"  Total losses: {pf_results['powers']['total_losses']:.2f} kW")
        print(f"  Voltage range: {min(pf_results['voltages'].values()):.3f} - {max(pf_results['voltages'].values()):.3f} p.u.")
        
        # Collect step results
        step_results = cosim_engine._collect_step_results(timestamp, pf_results, bdwpt_powers)
        print(f"✓ Step results collected with {len(step_results)} fields")
        print(f"  Keys: {sorted(step_results.keys())}")
        
        # Verify key data types
        print(f"  timestamp type: {type(step_results['timestamp'])}")
        print(f"  total_load_kw: {step_results['total_load_kw']} ({type(step_results['total_load_kw'])})")
        print(f"  total_bdwpt_kw: {step_results['total_bdwpt_kw']} ({type(step_results['total_bdwpt_kw'])})")
        
        # Count voltage columns
        voltage_cols = [k for k in step_results.keys() if 'voltage_bus' in k]
        bdwpt_node_cols = [k for k in step_results.keys() if 'bdwpt_node' in k]
        print(f"  Voltage columns: {len(voltage_cols)} ({voltage_cols[:3]}...)")
        print(f"  BDWPT node columns: {len(bdwpt_node_cols)} ({bdwpt_node_cols[:3]}...)")
        
        results_data.append(step_results)
    
    print(f"\n" + "=" * 40)
    print("TESTING DATAFRAME COMPILATION")
    print("=" * 40)
    
    # Test DataFrame creation
    print(f"Creating DataFrame from {len(results_data)} steps...")
    df = pd.DataFrame(results_data)
    
    print(f"✓ DataFrame created successfully!")
    print(f"  Shape: {df.shape}")
    print(f"  Columns ({len(df.columns)}): {sorted(df.columns)}")
    
    # Check for missing data
    missing_data = df.isnull().sum()
    missing_cols = missing_data[missing_data > 0]
    if len(missing_cols) > 0:
        print(f"⚠️  Missing data in columns: {dict(missing_cols)}")
    else:
        print(f"✓ No missing data")
    
    # Show sample data
    print(f"\nFirst row sample:")
    for col in ['timestamp', 'total_load_kw', 'total_bdwpt_kw', 'voltage_bus_632', 'bdwpt_node_632_kw']:
        if col in df.columns:
            print(f"  {col}: {df[col].iloc[0]}")
    
    # Save debug DataFrame
    debug_file = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\debug_full_simulation.csv"
    df.to_csv(debug_file, index=False)
    print(f"\n✓ Saved debug results to: {debug_file}")
    
    # Test the _compile_results method
    print(f"\n" + "=" * 40)
    print("TESTING _compile_results METHOD")
    print("=" * 40)
    
    compiled_results = cosim_engine._compile_results(results_data, scenario)
    print(f"✓ Results compiled successfully!")
    print(f"  Keys: {compiled_results.keys()}")
    
    if 'timeseries' in compiled_results:
        df_compiled = compiled_results['timeseries']
        print(f"✓ Timeseries DataFrame shape: {df_compiled.shape}")
        print(f"  Columns: {sorted(df_compiled.columns)}")
        
        # Save compiled results
        compiled_file = r"d:\1st_year_PhD\EEA_2025\EEA2025_v1.4.1\output\results\debug_compiled_results.csv"
        df_compiled.to_csv(compiled_file, index=False)
        print(f"✓ Saved compiled results to: {compiled_file}")
    
    if 'summary' in compiled_results:
        print(f"✓ Summary statistics: {compiled_results['summary']}")
    
    print(f"\n" + "=" * 60)
    print("DEBUG COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
except Exception as e:
    import traceback
    print(f"\n✗ ERROR: {e}")
    print(f"Error type: {type(e)}")
    print("Full traceback:")
    traceback.print_exc()
