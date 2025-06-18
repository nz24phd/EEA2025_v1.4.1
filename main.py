# main.py - Main entry point for the BDWPT simulation
import os
import sys
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime

# --- START OF DIAGNOSTIC CODE ---
# 打印当前工作目录和脚本路径，帮助定位问题
script_path = os.path.abspath(__file__)
current_working_dir = os.getcwd()
print(f"--- SCRIPT STARTUP DIAGNOSTICS ---")
print(f"Script Location: {script_path}")
print(f"Current Working Directory: {current_working_dir}")
print(f"Python Executable: {sys.executable}")
print(f"------------------------------------")
# --- END OF DIAGNOSTIC CODE ---


# Import custom modules
from config import SimulationConfig
from traffic_model.data_loader import TrafficDataLoader
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
        logging.FileHandler('simulation.log', mode='w'), # Use 'w' to overwrite log each time
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
        
        # Initialize data loader first
        logger.info("Setting up data loader...")
        data_loader = TrafficDataLoader(self.config.data_dir)

        # Initialize traffic model
        logger.info("Setting up traffic model...")
        self.traffic_model = TrafficModel(self.config, data_loader)
        
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
        """Run all scenarios"""
        all_results = {}
        scenarios_to_run = self.scenario_manager.get_all_scenarios_to_run()
        
        for scenario in scenarios_to_run:
            key = scenario['name']
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting: {key}")
            logger.info(f"{'='*60}")
            
            try:
                results = self.run_scenario(scenario['base_name'], scenario['bdwpt_penetration'])
                all_results[key] = results
                self.save_results(results, key)
            except Exception as e:
                logger.error(f"FATAL ERROR in scenario {key}: {str(e)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise e
                
        return all_results
        
    def analyze_results(self, all_results):
        """Analyze simulation results and calculate KPIs"""
        logger.info("\nAnalyzing simulation results...")
        
        kpis = self.results_analyzer.calculate_kpis(all_results)
        
        logger.info("\n" + "="*25 + " KEY PERFORMANCE INDICATORS " + "="*25)
        kpi_data = []
        for scenario, metrics in kpis.items():
            kpi_data.append({
                'Scenario': scenario,
                'Peak Reduction (kW)': metrics.get('peak_reduction_kw', 0),
                'Loss Reduction (kWh)': metrics.get('loss_reduction_kwh', 0),
                'V2G Energy (kWh)': metrics.get('energy_from_v2g_kwh', 0),
                'Voltage Improvement': metrics.get('voltage_improvement', 0)
            })
        kpi_df = pd.DataFrame(kpi_data)
        logger.info("\n" + kpi_df.to_string())
        logger.info("="*78)
            
        return kpis
        
    def generate_visualizations(self, all_results, kpis):
        """Generate all required visualizations"""
        logger.info("\nGenerating visualizations...")
        
        figures_path = os.path.abspath(self.config.figures_dir)
        os.makedirs(figures_path, exist_ok=True)
        logger.info(f"Ensuring figures directory exists at: {figures_path}")

        self.visualizer.plot_load_curves(all_results)
        self.visualizer.plot_voltage_profiles(all_results)
        self.visualizer.plot_kpi_comparison(kpis)
        self.visualizer.plot_bdwpt_heatmap(all_results)
        
        logger.info(f"Visualizations have been saved to: {figures_path}")
        
    def save_results(self, results, scenario_name):
        """Save simulation results to CSV and text files."""
        try:
            clean_name = scenario_name.replace("%", "pct").replace(" ", "_")
            
            # Use absolute path for clarity
            base_output_dir = os.path.abspath(self.config.results_dir)
            output_dir = os.path.join(base_output_dir, clean_name)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Attempting to save results to absolute path: {output_dir}")
            
            # Save time series data
            if 'timeseries' in results and isinstance(results['timeseries'], pd.DataFrame):
                timeseries_file = os.path.join(output_dir, 'timeseries_data.csv')
                results['timeseries'].to_csv(timeseries_file, index=False)
                logger.info(f"SUCCESS: Saved timeseries data to {timeseries_file}")
            
            # Save summary statistics
            if 'summary' in results:
                summary_file = os.path.join(output_dir, 'summary.txt')
                with open(summary_file, 'w') as f:
                    f.write(f"Scenario: {scenario_name}\n")
                    f.write(f"Simulation completed at: {datetime.now()}\n")
                    # ... (rest of summary writing)
                logger.info(f"SUCCESS: Saved summary to {summary_file}")
            
        except Exception as e:
            logger.error(f"CRITICAL FAILURE during file save for {scenario_name}: {e}")
            import traceback
            logger.error(f"Save traceback: {traceback.format_exc()}")
            raise e
            
    def run(self):
        """Main execution method"""
        logger.info("\n" + "="*80)
        logger.info("BDWPT SIMULATION PLATFORM FOR NEW ZEALAND LV NETWORKS")
        logger.info("="*80 + "\n")
        
        try:
            self.initialize()
            all_results = self.run_all_scenarios()
            
            if not all_results:
                logger.warning("No results were generated. Exiting analysis.")
                return

            kpis = self.analyze_results(all_results)
            self.generate_visualizations(all_results, kpis)
            
            logger.info("\n" + "="*80)
            logger.info("SIMULATION COMPLETED SUCCESSFULLY!")
            logger.info(f"Please find your results in: {os.path.abspath(self.config.output_dir)}")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"A fatal error occurred during the simulation run: {str(e)}")
            raise

if __name__ == "__main__":
    platform = BDWPTSimulationPlatform()
    platform.run()