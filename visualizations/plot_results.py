# visualizations/plot_results.py - Visualization functions for results

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import os

class Visualizer:
    """Create visualizations for BDWPT simulation results"""
    
    def __init__(self, config):
        self.config = config
        self.output_dir = config.figures_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def plot_load_curves(self, all_results):
        """Plot 24-hour load curves comparison"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        scenarios = ['Weekday Peak', 'Weekend Peak']
        
        for idx, scenario_base in enumerate(scenarios):
            ax = axes[idx]
            
            # Plot for different penetration levels
            for penetration in [0, 15, 40]:
                key = f"{scenario_base}_{penetration}%"
                if key in all_results:
                    df = all_results[key]['timeseries']
                    
                    # Resample to 15-minute intervals for cleaner plot
                    df_resampled = df.set_index('timestamp').resample('15min').mean()
                    
                    label = f"{penetration}% BDWPT" if penetration > 0 else "Baseline"
                    ax.plot(df_resampled.index, df_resampled['total_load_kw'], 
                           label=label, linewidth=2)
                    
            ax.set_title(f'{scenario_base} - Total Load Comparison', fontsize=14)
            ax.set_xlabel('Time of Day', fontsize=12)
            ax.set_ylabel('Total Load (kW)', fontsize=12)
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'load_curves_comparison.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_voltage_profiles(self, all_results):
        """Plot voltage profiles at critical buses"""
        # Select critical buses (e.g., end of feeder)
        critical_buses = [671, 675, 652, 611]  # End buses in IEEE 13
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for idx, bus in enumerate(critical_buses):
            ax = axes[idx]
            
            for key in ['Weekday Peak_0%', 'Weekday Peak_15%', 'Weekday Peak_40%']:
                if key in all_results:
                    df = all_results[key]['timeseries']
                    voltage_col = f'voltage_bus_{bus}'
                    
                    if voltage_col in df.columns:
                        # Resample to 15-minute intervals
                        df_resampled = df.set_index('timestamp').resample('15min').mean()
                        
                        penetration = key.split('_')[1]
                        label = f"{penetration} BDWPT" if penetration != "0%" else "Baseline"
                        
                        ax.plot(df_resampled.index, df_resampled[voltage_col], 
                               label=label, linewidth=2)
                        
            # Add voltage limits
            ax.axhline(y=1.05, color='r', linestyle='--', alpha=0.5, label='Upper Limit')
            ax.axhline(y=0.95, color='r', linestyle='--', alpha=0.5, label='Lower Limit')
            
            ax.set_title(f'Bus {bus} Voltage Profile', fontsize=12)
            ax.set_xlabel('Time of Day', fontsize=10)
            ax.set_ylabel('Voltage (p.u.)', fontsize=10)
            ax.set_ylim(0.94, 1.06)
            ax.legend(loc='best', fontsize=8)
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'voltage_profiles.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_kpi_comparison(self, kpis):
        """Plot KPI comparison bar charts"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        # Prepare data for plotting
        scenarios = []
        peak_reductions = []
        voltage_improvements = []
        loss_reductions = []
        v2g_energy = []
        
        for key, kpi in kpis.items():
            if "0%" not in key:  # Skip baseline
                scenarios.append(key.replace("_", "\n"))
                peak_reductions.append(kpi['peak_reduction_kw'])
                voltage_improvements.append(kpi['voltage_improvement'])
                loss_reductions.append(kpi['loss_reduction_kwh'])
                v2g_energy.append(kpi['energy_from_v2g_kwh'])
                  # Plot 1: Peak Load Reduction
        ax = axes[0]
        bars = ax.bar(scenarios, peak_reductions, color='steelblue')
        ax.set_title('Peak Load Reduction', fontsize=14)
        ax.set_ylabel('Reduction (kW)', fontsize=12)
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')
                   
        # Plot 2: Voltage Violation Reduction
        ax = axes[1]
        bars = ax.bar(scenarios, voltage_improvements, color='darkgreen')
        ax.set_title('Voltage Violation Reduction', fontsize=14)
        ax.set_ylabel('Violations Reduced', fontsize=12)
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        # Plot 3: Loss Reduction
        ax = axes[2]
        bars = ax.bar(scenarios, loss_reductions, color='darkorange')
        ax.set_title('Energy Loss Reduction', fontsize=14)
        ax.set_ylabel('Reduction (kWh)', fontsize=12)
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        # Plot 4: V2G Energy Contribution
        ax = axes[3]
        bars = ax.bar(scenarios, v2g_energy, color='darkred')
        ax.set_title('V2G Energy Contribution', fontsize=14)
        ax.set_ylabel('Energy (kWh)', fontsize=12)
        ax.set_xticks(range(len(scenarios)))
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'kpi_comparison.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
    def plot_bdwpt_heatmap(self, all_results):
        """Plot heatmap of BDWPT power exchange by node and time"""
        # Select one scenario for detailed view
        key = 'Weekday Peak_40%'
        if key not in all_results:
            return
            
        df = all_results[key]['timeseries']
        
        # Extract BDWPT power columns
        bdwpt_cols = [col for col in df.columns if 'bdwpt_node' in col]
        if not bdwpt_cols:
            return
            
        # Create matrix for heatmap
        nodes = sorted([int(col.split('_')[2]) for col in bdwpt_cols])
        
        # Resample to hourly for cleaner visualization
        df_hourly = df.set_index('timestamp').resample('h').mean()
        
        # Create power matrix
        power_matrix = np.zeros((24, len(nodes)))
        
        for i, hour in enumerate(range(24)):
            for j, node in enumerate(nodes):
                col = f'bdwpt_node_{node}_kw'
                if col in df_hourly.columns:
                    hour_data = df_hourly[df_hourly.index.hour == hour][col]
                    if not hour_data.empty:
                        power_matrix[i, j] = hour_data.mean()
                        
        # Create heatmap
        plt.figure(figsize=(12, 8))
        
        # Use diverging colormap (red for discharge, blue for charge)
        sns.heatmap(power_matrix, 
                   xticklabels=nodes,
                   yticklabels=range(24),
                   cmap='RdBu_r',
                   center=0,
                   vmin=-30,
                   vmax=50,
                   cbar_kws={'label': 'Power (kW)\n← V2G | G2V →'},
                   annot=False)
        
        plt.title('BDWPT Power Exchange Heatmap (40% Penetration, Weekday)', fontsize=14)
        plt.xlabel('Node Number', fontsize=12)
        plt.ylabel('Hour of Day', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'bdwpt_power_heatmap.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
