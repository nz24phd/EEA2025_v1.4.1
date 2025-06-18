#!/usr/bin/env python3

import logging
import sys

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("DEBUGGING MAIN SIMULATION RESULTS")
print("=" * 50)

try:
    from main import BDWPTSimulationPlatform
    
    # Initialize platform
    platform = BDWPTSimulationPlatform()
    
    # Run just one scenario to check results
    print("Running single test scenario...")
    
    results = platform.run_scenario("Weekday Peak", 15)
    
    print(f"Results type: {type(results)}")
    print(f"Results keys: {results.keys() if hasattr(results, 'keys') else 'No keys method'}")
    
    if isinstance(results, dict):
        if 'timeseries' in results:
            df = results['timeseries']
            print(f"\nTimeseries DataFrame:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Sample data:")
            print(df.head(2))
            
            # Check for missing columns
            expected_cols = ['timestamp', 'total_load_kw', 'total_bdwpt_kw', 'voltage_bus_632']
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                print(f"  ⚠️  Missing expected columns: {missing_cols}")
            else:
                print(f"  ✓ All expected columns present")
        
        if 'summary' in results:
            print(f"\nSummary:")
            print(f"  Keys: {results['summary'].keys()}")
            print(f"  Sample values: {dict(list(results['summary'].items())[:5])}")
    
    else:
        print(f"Unexpected results type: {type(results)}")
        print(f"Results content: {results}")

except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Full traceback:")
    traceback.print_exc()
