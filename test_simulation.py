#!/usr/bin/env python3

import logging
import pandas as pd

logging.basicConfig(level=logging.DEBUG)

# Test just one scenario
print("Testing single scenario simulation...")

try:
    from config import SimulationConfig
    from traffic_model.data_loader import TrafficDataLoader
    from traffic_model.main_traffic import TrafficModel
    from power_grid_model.ieee_13_bus_model import IEEE13BusSystem
    from cosimulation.simulation_engine import CoSimulationEngine
    from cosimulation.scenarios import ScenarioManager
    
    print("✓ All imports successful")
    
    # Initialize components
    config = SimulationConfig()
    data_loader = TrafficDataLoader(config.data_dir)
    traffic_model = TrafficModel(config, data_loader)
    power_grid = IEEE13BusSystem(config)
    power_grid.build_network()
    
    # Test co-simulation for one scenario
    cosim_engine = CoSimulationEngine(config, traffic_model, power_grid)
    scenario_manager = ScenarioManager(config)
    
    scenario = scenario_manager.get_scenario("Weekday Peak", 15)
    print(f"Testing scenario: {scenario}")
    
    # Run just a few time steps
    print("Running simulation...")
    results = cosim_engine.run_simulation(scenario)
    
    print(f"Results type: {type(results)}")
    print(f"Results keys: {results.keys()}")
    
    if 'timeseries' in results:
        df = results['timeseries']
        print(f"Timeseries shape: {df.shape}")
        print(f"Timeseries columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head())
        
        # Check for BDWPT data
        bdwpt_cols = [col for col in df.columns if 'bdwpt' in col.lower()]
        print(f"BDWPT columns: {bdwpt_cols}")
        
        if bdwpt_cols:
            print("BDWPT data sample:")
            for col in bdwpt_cols:
                print(f"  {col}: {df[col].sum():.2f} total")
    
    if 'summary' in results:
        print(f"Summary: {results['summary']}")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
