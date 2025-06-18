# NZ_BDWPT_Simulation Platform
# Main entry point and project structure

"""
Project Structure:
/NZ_BDWPT_Simulation
|-- /1_traffic_model
|   |-- data_loader.py
|   |-- trip_generator.py
|   |-- vehicle_movement.py
|   |-- main_traffic.py
|-- /2_power_grid_model
|   |-- ieee_13_bus_model.py
|   |-- bdwpt_agent.py
|-- /3_cosimulation
|   |-- simulation_engine.py
|   |-- scenarios.py
|   |-- results_analyzer.py
|-- /4_visualizations
|   |-- plot_results.py
|-- main.py
|-- config.py
"""

# main.py - Main entry point for the simulation
import os
import sys
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime

# Import custom modules
from config import SimulationConfig
from traffic_model.main_traffic import TrafficModel
from power_grid_model.ieee_13_bus_model import IEEE13BusSystem
from cosimulation.simulation_engine import CoSimulationEngine
from cosimulation.scenarios import ScenarioManager
from cosimulation.results_analyzer import ResultsAnalyzer
from visualizations.plot_results import Visualizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BDWPTSimulationPlatform:
    """Main simulation platform for BDWPT in urban LV networks"""
    
    def __init__(self):
        self.config = SimulationConfig()
        self.traffic_model = None
        self.power_grid = None
        self.cosim_engine = None
        self.scenario_manager = None
        self.results_analyzer = None
        self.visualizer = None
        
    def initialize(self):
        """Initialize all simulation components"""
        logger.info("Initializing BDWPT Simulation Platform...")
        
        # Initialize traffic model
        logger.info("Setting up traffic model...")
        self.traffic_model = TrafficModel(self.config)
        
        # Initialize power grid model
        logger.info("Setting up IEEE 13-bus test system...")
        self.power_grid = IEEE13BusSystem(self.config)
        self.power_grid.build_network()
        
        # Initialize co-simulation engine
        logger.info("Setting up co-simulation engine...")
        self.cosim_engine = CoSimulationEngine(
            self.config,
            self.traffic_model,
            self.power_grid
        )
        
        # Initialize scenario manager
        self.scenario_manager = ScenarioManager(self.config)
        
        # Initialize results analyzer and visualizer
        self.results_analyzer = ResultsAnalyzer(self.config)
        self.visualizer = Visualizer(self.config)
        
        logger.info("Initialization complete!")
        
    def run_scenario(self, scenario_name, bdwpt_penetration):
        """Run a single scenario with specified BDWPT penetration"""
        logger.info(f"Running scenario: {scenario_name} with {bdwpt_penetration}% BDWPT penetration")
        
        # Configure scenario
        scenario = self.scenario_manager.get_scenario(scenario_name, bdwpt_penetration)
        
        # Run co-simulation
        start_time = time.time()
        results = self.cosim_engine.run_simulation(scenario)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Simulation completed in {elapsed_time:.2f} seconds")
        
        return results
        
    def run_all_scenarios(self):
        """Run all scenarios (0%, 15%, 40% BDWPT penetration)"""
        all_results = {}
        
        # Define scenarios
        scenarios = [
            ("Weekday Peak", 0),    # Baseline
            ("Weekday Peak", 15),   # 15% BDWPT
            ("Weekday Peak", 40),   # 40% BDWPT
            ("Weekend Peak", 0),    # Baseline
            ("Weekend Peak", 15),   # 15% BDWPT
            ("Weekend Peak", 40),   # 40% BDWPT
        ]
        
        for scenario_name, penetration in scenarios:
            key = f"{scenario_name}_{penetration}%"
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting: {key}")
            logger.info(f"{'='*60}")
            
            try:
                results = self.run_scenario(scenario_name, penetration)
                all_results[key] = results
                
                # Save intermediate results
                self.save_results(results, key)
                
            except Exception as e:
                logger.error(f"Error in scenario {key}: {str(e)}")
                continue
                
        return all_results
        
    def analyze_results(self, all_results):
        """Analyze simulation results and calculate KPIs"""
        logger.info("\nAnalyzing simulation results...")
        
        kpis = self.results_analyzer.calculate_kpis(all_results)
        
        # Log key findings
        logger.info("\n=== KEY PERFORMANCE INDICATORS ===")
        for scenario, metrics in kpis.items():
            logger.info(f"\nScenario: {scenario}")
            logger.info(f"  Peak Load Reduction: {metrics['peak_reduction']:.2f} kW ({metrics['peak_reduction_pct']:.1f}%)")
            logger.info(f"  Voltage Violations: {metrics['voltage_violations']} hours")
            logger.info(f"  Energy Losses: {metrics['losses']:.2f} kWh")
            logger.info(f"  Reverse Power Flow Events: {metrics['reverse_flow_events']}")
            
        return kpis
        
    def generate_visualizations(self, all_results, kpis):
        """Generate all required visualizations"""
        logger.info("\nGenerating visualizations...")
        
        # 1. 24-hour load curve comparison
        self.visualizer.plot_load_curves(all_results)
        
        # 2. Voltage profile comparison
        self.visualizer.plot_voltage_profiles(all_results)
        
        # 3. KPI comparison charts
        self.visualizer.plot_kpi_comparison(kpis)
        
        # 4. Heatmap of BDWPT power exchange
        self.visualizer.plot_bdwpt_heatmap(all_results)
        
        logger.info("Visualizations saved to output directory")
        
    def save_results(self, results, scenario_name):
        """Save simulation results to CSV files"""
        output_dir = os.path.join(self.config.output_dir, scenario_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save time series data
        results['timeseries'].to_csv(
            os.path.join(output_dir, 'timeseries_data.csv'),
            index=False
        )
        
        # Save summary statistics
        with open(os.path.join(output_dir, 'summary.txt'), 'w') as f:
            f.write(f"Scenario: {scenario_name}\n")
            f.write(f"Simulation completed at: {datetime.now()}\n")
            f.write(f"Total simulation steps: {len(results['timeseries'])}\n")
            f.write(f"Peak load: {results['summary']['peak_load']:.2f} kW\n")
            f.write(f"Min voltage: {results['summary']['min_voltage']:.3f} p.u.\n")
            f.write(f"Max voltage: {results['summary']['max_voltage']:.3f} p.u.\n")
            
    def run(self):
        """Main execution method"""
        logger.info("\n" + "="*80)
        logger.info("BDWPT SIMULATION PLATFORM FOR NEW ZEALAND LV NETWORKS")
        logger.info("="*80 + "\n")
        
        try:
            # Initialize platform
            self.initialize()
            
            # Run all scenarios
            all_results = self.run_all_scenarios()
            
            # Analyze results
            kpis = self.analyze_results(all_results)
            
            # Generate visualizations
            self.generate_visualizations(all_results, kpis)
            
            logger.info("\n" + "="*80)
            logger.info("SIMULATION COMPLETED SUCCESSFULLY!")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Create and run simulation platform
    platform = BDWPTSimulationPlatform()
    platform.run()