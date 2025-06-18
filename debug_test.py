#!/usr/bin/env python3

import sys
import traceback
import logging

logging.basicConfig(level=logging.DEBUG)

# Test imports and basic functionality
print("Starting debug test...")

try:
    print("1. Testing config import...")
    from config import SimulationConfig
    config = SimulationConfig()
    print(f"✓ Config loaded successfully")
    print(f"BDWPT nodes: {config.grid_params['bdwpt_nodes']}")
    
    print("2. Testing power grid import...")
    from power_grid_model.ieee_13_bus_model import IEEE13BusSystem
    power_grid = IEEE13BusSystem(config)
    print(f"✓ IEEE13BusSystem created")
    
    print("3. Building network...")
    power_grid.build_network()
    print(f"✓ Power grid built successfully")
    print(f"Available buses: {list(power_grid.buses.keys())}")
    
    print("4. Testing BDWPT load addition...")
    test_node = 632
    print(f"Testing BDWPT load addition to node {test_node}")
    power_grid.add_bdwpt_load(test_node, 50.0)
    
    print("5. Testing voltage retrieval...")
    voltage = power_grid.get_voltage(test_node)
    print(f"✓ Voltage at node {test_node}: {voltage}")
    print(f"Voltage type: {type(voltage)}")
    
    print("6. Testing BDWPT agent import...")
    from power_grid_model.bdwpt_agent import BDWPTAgent
    agent = BDWPTAgent('test_vehicle', 60, config)
    print(f"✓ BDWPT agent created successfully")
    
    print("7. Testing agent action...")
    action = agent.decide_action(1.0, 20.0, 15)
    print(f"✓ Agent action: {action}")
    print(f"Action type: {type(action)}")
    print(f"Action keys: {action.keys() if hasattr(action, 'keys') else 'N/A'}")
    
    if 'power_kw' in action:
        print(f"Power value: {action['power_kw']}")
        print(f"Power type: {type(action['power_kw'])}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e)}")
    traceback.print_exc()
