#!/usr/bin/env python3
"""
Test the fixed simulation engine with data flow debugging
"""

import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("TESTING FIXED SIMULATION ENGINE")
print("=" * 60)

try:
    # Import components
    from main import BDWPTSimulationPlatform
    
    # Initialize platform
    logger.info("Initializing simulation platform...")
    platform = BDWPTSimulationPlatform()
    
    # Run a single scenario test
    logger.info("Running test scenario: Weekday Peak 15%...")
    results = platform.run_scenario("Weekday Peak", 15)
    
    logger.info("✓ Simulation completed successfully!")
    
    # Analyze results
    print(f"\nRESULT ANALYSIS:")
    print(f"Result type: {type(results)}")
    print(f"Result keys: {list(results.keys())}")
    
    if 'timeseries' in results:
        df = results['timeseries']
        print(f"\nTimeseries DataFrame:")
        print(f"  Shape: {df.shape}")
        print(f"  Columns ({len(df.columns)}): {list(df.columns)}")
        
        # Show sample data
        print(f"\nSample data:")
        print(df.head(3))
        
        # Check for expected columns
        expected_cols = ['timestamp', 'total_load_kw', 'total_bdwpt_kw', 'voltage_bus_632']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        if missing_cols:
            print(f"  ⚠️  Missing expected columns: {missing_cols}")
        else:
            print(f"  ✓ All key columns present!")
        
        # Check for proper data
        if df.shape[1] > 5:  # Should have many columns
            print(f"  ✓ DataFrame has proper number of columns ({df.shape[1]})")
        else:
            print(f"  ⚠️  DataFrame still has too few columns ({df.shape[1]})")
        
        # Save fixed test results
        test_file = os.path.join("output", "results", "test_fixed_simulation.csv")
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        df.to_csv(test_file, index=False)
        print(f"  ✓ Saved test results to: {test_file}")
    
    if 'summary' in results:
        summary = results['summary']
        print(f"\nSummary Statistics:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
    
    print(f"\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
except Exception as e:
    import traceback
    print(f"\n✗ ERROR: {e}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)
