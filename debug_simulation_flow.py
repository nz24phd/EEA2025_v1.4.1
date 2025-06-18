#!/usr/bin/env python3

import sys
import traceback
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

print("Testing simulation data flow...")

try:
    print("1. Setting up components...")
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
    
    print("✓ All components initialized")
    
    print("2. Testing scenario creation...")
    scenario = scenario_manager.get_scenario("Weekday Peak", 15)
    print(f"✓ Scenario: {scenario}")
    
    print("3. Testing one simulation step...")
    
    # Configure traffic model
    traffic_model.set_bdwpt_penetration(15)
    
    # Test BDWPT power calculation
    bdwpt_powers = cosim_engine._calculate_bdwpt_powers(8)  # 8 AM
    print(f"✓ BDWPT powers calculated: {bdwpt_powers}")
    print(f"Total BDWPT power: {sum(bdwpt_powers.values()):.2f} kW")
    
    # Test grid load update
    cosim_engine._update_grid_loads(8, "Weekday Peak", bdwpt_powers)
    print("✓ Grid loads updated")
    
    # Test power flow solution
    pf_results = power_grid.solve_power_flow()
    print(f"✓ Power flow results: {pf_results}")
    
    # Test results collection
    from datetime import datetime
    timestamp = datetime(2024, 1, 1, 8, 0)
    step_results = cosim_engine._collect_step_results(timestamp, pf_results, bdwpt_powers)
    print(f"✓ Step results collected")
    print(f"Step results keys: {step_results.keys()}")
    print(f"Total load: {step_results.get('total_load_kw', 'N/A')}")
    print(f"Total BDWPT: {step_results.get('total_bdwpt_kw', 'N/A')}")
    print(f"BDWPT charging: {step_results.get('bdwpt_charging_kw', 'N/A')}")
    print(f"BDWPT discharging: {step_results.get('bdwpt_discharging_kw', 'N/A')}")
    
    # Check voltage data
    voltage_keys = [k for k in step_results.keys() if 'voltage' in k]
    print(f"Voltage data keys: {voltage_keys}")
    
    # Check BDWPT node data
    bdwpt_keys = [k for k in step_results.keys() if 'bdwpt_node' in k]
    print(f"BDWPT node data keys: {bdwpt_keys}")
    
    print("4. Testing full simulation (short)...")
    
    # Modify scenario to run only 3 time steps for testing
    test_scenario = scenario.copy()
    test_scenario['simulation_hours'] = 1  # Just 1 hour = 4 time steps
    
    results = cosim_engine.run_simulation(test_scenario)
    print(f"✓ Simulation completed")
    print(f"Results type: {type(results)}")
    print(f"Results keys: {results.keys()}")
    
    if 'timeseries' in results:
        df = results['timeseries']
        print(f"✓ Timeseries DataFrame shape: {df.shape}")
        print(f"Timeseries columns: {list(df.columns)}")
        
        # Check data content
        if 'total_load_kw' in df.columns:
            print(f"Load range: {df['total_load_kw'].min():.2f} - {df['total_load_kw'].max():.2f} kW")
        
        if 'total_bdwpt_kw' in df.columns:
            print(f"BDWPT range: {df['total_bdwpt_kw'].min():.2f} - {df['total_bdwpt_kw'].max():.2f} kW")
            print(f"BDWPT sum: {df['total_bdwpt_kw'].sum():.2f} kW")
        
        # Show first few rows
        print("First few rows:")
        print(df.head(3))
        
    if 'summary' in results:
        print(f"✓ Summary data: {results['summary']}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e)}")
    traceback.print_exc()
