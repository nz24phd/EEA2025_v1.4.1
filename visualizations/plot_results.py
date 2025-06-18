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
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
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
                    df_resampled = df.set_index('timestamp').resample('15T').mean()
                    
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
                        df_resampled = df.set_index('timestamp').resample('15T').mean()
                        
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
                peak_reductions.append(kpi['peak_reduction'])
                voltage_improvements.append(kpi['voltage_improvement'])
                loss_reductions.append(kpi['loss_reduction'])
                v2g_energy.append(kpi['energy_from_v2g'])
                
        # Plot 1: Peak Load Reduction
        ax = axes[0]
        bars = ax.bar(scenarios, peak_reductions, color='steelblue')
        ax.set_title('Peak Load Reduction', fontsize=14)
        ax.set_ylabel('Reduction (kW)', fontsize=12)
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
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        # Plot 3: Loss Reduction
        ax = axes[2]
        bars = ax.bar(scenarios, loss_reductions, color='darkorange')
        ax.set_title('Energy Loss Reduction', fontsize=14)
        ax.set_ylabel('Reduction (kWh)', fontsize=12)
        ax.set_xticklabels(scenarios, rotation=45, ha='right')
        
        # Plot 4: V2G Energy Contribution
        ax = axes[3]
        bars = ax.bar(scenarios, v2g_energy, color='darkred')
        ax.set_title('V2G Energy Contribution', fontsize=14)
        ax.set_ylabel('Energy (kWh)', fontsize=12)
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
        df_hourly = df.set_index('timestamp').resample('H').mean()
        
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
        
    def plot_soc_distribution(self, all_results):
        """Plot SoC distribution of BDWPT vehicles"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        for idx, penetration in enumerate([15, 40]):
            ax = axes[idx]
            key = f'Weekday Peak_{penetration}%'
            
            if key in all_results and all_results[key]['agent_stats'] is not None:
                agent_stats = all_results[key]['agent_stats']
                
                # Plot histogram of final SoC
                ax.hist(agent_stats['final_soc'], bins=20, alpha=0.7, 
                       color='skyblue', edgecolor='black')
                ax.axvline(agent_stats['final_soc'].mean(), color='red', 
                          linestyle='--', linewidth=2, label=f'Mean: {agent_stats["final_soc"].mean():.2f}')
                
                ax.set_title(f'Final SoC Distribution ({penetration}% BDWPT)', fontsize=12)
                ax.set_xlabel('State of Charge', fontsize=10)
                ax.set_ylabel('Number of Vehicles', fontsize=10)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'soc_distribution.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
    def create_summary_report(self, all_results, kpis):
        """Create a summary report figure"""
        fig = plt.figure(figsize=(16, 10))
        
        # Create grid for subplots
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Main load curve plot
        ax1 = fig.add_subplot(gs[0:2, 0:2])
        self._plot_main_load_curve(ax1, all_results)
        
        # KPI summary table
        ax2 = fig.add_subplot(gs[0:2, 2])
        self._plot_kpi_table(ax2, kpis)
        
        # Peak reduction bar chart
        ax3 = fig.add_subplot(gs[2, 0])
        self._plot_peak_reduction_summary(ax3, kpis)
        
        # Voltage improvement
        ax4 = fig.add_subplot(gs[2, 1])
        self._plot_voltage_improvement_summary(ax4, kpis)
        
        # Energy exchange pie chart
        ax5 = fig.add_subplot(gs[2, 2])
        self._plot_energy_exchange_summary(ax5, all_results)
        
        fig.suptitle('BDWPT Simulation Summary Report - Wellington LV Network', 
                    fontsize=16, fontweight='bold')
        
        plt.savefig(os.path.join(self.output_dir, 'summary_report.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
    def _plot_main_load_curve(self, ax, all_results):
        """Plot main load curve for summary"""
        for penetration in [0, 15, 40]:
            key = f"Weekday Peak_{penetration}%"
            if key in all_results:
                df = all_results[key]['timeseries']
                df_resampled = df.set_index('timestamp').resample('30T').mean()
                
                label = f"{penetration}% BDWPT" if penetration > 0 else "Baseline"
                ax.plot(df_resampled.index, df_resampled['total_load_kw'], 
                       label=label, linewidth=2.5)
                       
        ax.set_title('Daily Load Profile Comparison', fontsize=14)
        ax.set_xlabel('Time of Day', fontsize=12)
        ax.set_ylabel('Total Load (kW)', fontsize=12)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
    def _plot_kpi_table(self, ax, kpis):
        """Create KPI summary table"""
        ax.axis('tight')
        ax.axis('off')
        
        # Prepare table data
        headers = ['Scenario', 'Peak\nReduction\n(%)', 'Voltage\nViolations\nReduced', 
                  'V2G Energy\n(kWh)']
        
        table_data = []
        for key, kpi in kpis.items():
            if "0%" not in key and "Weekday" in key:
                row = [
                    key.split('_')[1],
                    f"{kpi['peak_reduction_pct']:.1f}%",
                    f"{kpi['voltage_improvement']}",
                    f"{kpi['energy_from_v2g']:.0f}"
                ]
                table_data.append(row)
                
        table = ax.table(cellText=table_data, colLabels=headers, 
                        loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        ax.set_title('Key Performance Indicators', fontsize=12, pad=20)
        
    def _plot_peak_reduction_summary(self, ax, kpis):
        """Plot peak reduction summary"""
        scenarios = []
        reductions = []
        
        for key, kpi in kpis.items():
            if "0%" not in key and "Weekday" in key:
                scenarios.append(key.split('_')[1])
                reductions.append(kpi['peak_reduction_pct'])
                
        bars = ax.bar(scenarios, reductions, color='steelblue')
        ax.set_title('Peak Load Reduction', fontsize=10)
        ax.set_ylabel('Reduction (%)', fontsize=9)
        ax.set_xlabel('BDWPT Penetration', fontsize=9)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
                   
    def _plot_voltage_improvement_summary(self, ax, kpis):
        """Plot voltage improvement summary"""
        scenarios = []
        improvements = []
        
        for key, kpi in kpis.items():
            if "0%" not in key and "Weekday" in key:
                scenarios.append(key.split('_')[1])
                improvements.append(kpi['voltage_improvement'])
                
        bars = ax.bar(scenarios, improvements, color='darkgreen')
        ax.set_title('Voltage Violations Reduced', fontsize=10)
        ax.set_ylabel('Count', fontsize=9)
        ax.set_xlabel('BDWPT Penetration', fontsize=9)
        
    def _plot_energy_exchange_summary(self, ax, all_results):
        """Plot energy exchange pie chart"""
        key = 'Weekday Peak_40%'
        if key in all_results:
            summary = all_results[key]['summary']
            
            g2v = summary['bdwpt_energy_charged_kwh']
            v2g = summary['bdwpt_energy_discharged_kwh']
            
            sizes = [g2v, v2g]
            labels = ['G2V Charging', 'V2G Discharging']
            colors = ['lightblue', 'lightcoral']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                  startangle=90)
            ax.set_title('BDWPT Energy Exchange\n(40% Penetration)', fontsize=10)