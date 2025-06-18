# power_grid_model/ieee_13_bus_model.py - IEEE 13-bus test system with BDWPT

import numpy as np
import pandas as pd
import logging
try:
    import py_dss_interface
    USE_OPENDSS = True
except ImportError:
    USE_OPENDSS = False
    logging.warning("OpenDSS not available, using simplified power flow")

logger = logging.getLogger(__name__)

class IEEE13BusSystem:
    """IEEE 13-bus test feeder with BDWPT integration"""
    
    def __init__(self, config):
        self.config = config
        self.buses = {}
        self.lines = {}
        self.loads = {}
        self.bdwpt_loads = {}
        self.voltages = {}
        self.power_flows = {}
        
        if USE_OPENDSS:
            self.dss = py_dss_interface.DSS()
        else:
            self.dss = None
            
    def build_network(self):
        """Build IEEE 13-bus test system"""
        logger.info("Building IEEE 13-bus test system...")
        
        if USE_OPENDSS:
            self._build_opendss_model()
        else:
            self._build_simple_model()
            
    def _build_opendss_model(self):
        """Build model using OpenDSS"""
        # Clear any existing circuit
        self.dss.text("clear")
        
        # Create new circuit
        self.dss.text("new circuit.IEEE13 basekv=4.16 pu=1.00 phases=3 bus1=650")
        
        # Define line codes
        self._define_line_codes()
        
        # Add lines
        self._add_lines()
        
        # Add loads
        self._add_loads()
        
        # Add capacitors
        self._add_capacitors()
        
        # Add transformer
        self.dss.text("New Transformer.SubXF Phases=3 Windings=2 Xhl=0.01")
        self.dss.text("~ wdg=1 bus=650 kv=4.16 kva=5000 %r=0.0005")
        self.dss.text("~ wdg=2 bus=RG60 kv=4.16 kva=5000 %r=0.0005")
        
        # Solve initial power flow
        self.dss.text("set voltagebases=[4.16]")
        self.dss.text("calcvoltagebases")
        self.dss.solution.solve()
        
        logger.info("OpenDSS model built successfully")
        
    def _build_simple_model(self):
        """Build simplified model for testing without OpenDSS"""
        # Define buses
        self.buses = {
            650: {'phases': 3, 'voltage_kv': 4.16, 'type': 'slack'},
            632: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            633: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            634: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            645: {'phases': 2, 'voltage_kv': 4.16, 'type': 'pq'},
            646: {'phases': 2, 'voltage_kv': 4.16, 'type': 'pq'},
            671: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            680: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            684: {'phases': 1, 'voltage_kv': 4.16, 'type': 'pq'},
            611: {'phases': 1, 'voltage_kv': 4.16, 'type': 'pq'},
            652: {'phases': 1, 'voltage_kv': 4.16, 'type': 'pq'},
            692: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
            675: {'phases': 3, 'voltage_kv': 4.16, 'type': 'pq'},
        }
        
        # Initialize voltages (p.u.)
        for bus in self.buses:
            self.voltages[bus] = 1.0
            
        # Define base loads (kW)
        self.loads = {
            634: {'P': 160, 'Q': 110},
            645: {'P': 0, 'Q': 0},
            646: {'P': 230, 'Q': 132},
            652: {'P': 128, 'Q': 86},
            671: {'P': 385, 'Q': 220},
            675: {'P': 485, 'Q': 190},
            692: {'P': 0, 'Q': 0},
            611: {'P': 170, 'Q': 80},
        }
        
        logger.info("Simple model built successfully")
        
    def _define_line_codes(self):
        """Define line codes for OpenDSS"""
        # Line code definitions from IEEE 13-bus test case
        line_codes = [
            "New linecode.601 nphases=3 r1=0.3465 x1=1.0179 r0=0.7876 x0=1.2133 c1=11.155 c0=5.3302 units=mi",
            "New linecode.602 nphases=3 r1=0.7526 x1=1.1814 r0=1.1681 x0=1.4751 c1=11.389 c0=5.4246 units=mi",
            "New linecode.603 nphases=2 r1=1.3294 x1=1.3471 r0=1.6565 x0=1.6916 c1=10.374 c0=4.9055 units=mi",
            "New linecode.604 nphases=2 r1=1.3238 x1=1.3569 r0=1.6559 x0=1.7023 c1=10.348 c0=4.8928 units=mi",
            "New linecode.605 nphases=1 r1=1.3292 x1=1.3475 r0=1.6559 x0=1.6895 c1=10.362 c0=4.8998 units=mi",
        ]
        
        for code in line_codes:
            self.dss.text(code)
            
    def _add_lines(self):
        """Add lines to OpenDSS model"""
        lines = [
            "New Line.650632 Phases=3 Bus1=650.1.2.3 Bus2=632.1.2.3 LineCode=601 Length=2000 units=ft",
            "New Line.632670 Phases=3 Bus1=632.1.2.3 Bus2=670.1.2.3 LineCode=601 Length=667 units=ft",
            "New Line.670671 Phases=3 Bus1=670.1.2.3 Bus2=671.1.2.3 LineCode=601 Length=1333 units=ft",
            "New Line.671680 Phases=3 Bus1=671.1.2.3 Bus2=680.1.2.3 LineCode=601 Length=1000 units=ft",
            "New Line.632633 Phases=3 Bus1=632.1.2.3 Bus2=633.1.2.3 LineCode=602 Length=500 units=ft",
            "New Line.632645 Phases=2 Bus1=632.3.2 Bus2=645.3.2 LineCode=603 Length=500 units=ft",
            "New Line.645646 Phases=2 Bus1=645.3.2 Bus2=646.3.2 LineCode=603 Length=300 units=ft",
            "New Line.692675 Phases=3 Bus1=692.1.2.3 Bus2=675.1.2.3 LineCode=601 Length=1000 units=ft",
            "New Line.684611 Phases=1 Bus1=684.3 Bus2=611.3 LineCode=605 Length=300 units=ft",
            "New Line.684652 Phases=1 Bus1=684.1 Bus2=652.1 LineCode=605 Length=800 units=ft",
        ]
        
        for line in lines:
            self.dss.text(line)
            
    def _add_loads(self):
        """Add loads to OpenDSS model"""
        loads = [
            "New Load.634 Bus1=634.1.2.3 Phases=3 Conn=Wye Model=1 kV=4.16 kW=160 kvar=110",
            "New Load.645 Bus1=645.2.3 Phases=2 Conn=Wye Model=1 kV=4.16 kW=0 kvar=0",
            "New Load.646 Bus1=646.2.3 Phases=2 Conn=Delta Model=2 kV=4.16 kW=230 kvar=132",
            "New Load.652 Bus1=652.1 Phases=1 Conn=Wye Model=2 kV=2.4 kW=128 kvar=86",
            "New Load.671 Bus1=671.1.2.3 Phases=3 Conn=Delta Model=1 kV=4.16 kW=385 kvar=220",
            "New Load.675 Bus1=675.1.2.3 Phases=3 Conn=Wye Model=1 kV=4.16 kW=485 kvar=190",
            "New Load.692 Bus1=692.3 Phases=1 Conn=Delta Model=5 kV=4.16 kW=0 kvar=0",
            "New Load.611 Bus1=611.3 Phases=1 Conn=Wye Model=5 kV=2.4 kW=170 kvar=80",
        ]
        
        for load in loads:
            self.dss.text(load)
            
    def _add_capacitors(self):
        """Add capacitors to OpenDSS model"""
        caps = [
            "New Capacitor.Cap1 Bus1=675 phases=3 kvar=600",
            "New Capacitor.Cap2 Bus1=611.3 phases=1 kvar=100",
        ]
        
        for cap in caps:
            self.dss.text(cap)
            
    def add_bdwpt_load(self, bus_id, power_kw, power_factor=0.95):
        """Add BDWPT load/generation at a specific bus"""
        if bus_id not in self.buses:
            logger.warning(f"Bus {bus_id} not found in network")
            return
            
        # Create unique BDWPT load name
        bdwpt_name = f"BDWPT_{bus_id}"
        
        if USE_OPENDSS:
            # Remove existing BDWPT load if any
            if bdwpt_name in self.bdwpt_loads:
                self.dss.text(f"disable load.{bdwpt_name}")
                
            # Add new BDWPT load (negative power for V2G)
            if power_kw != 0:
                kvar = power_kw * np.tan(np.arccos(power_factor))
                self.dss.text(f"New Load.{bdwpt_name} Bus1={bus_id} Phases=3 Conn=Wye Model=1 kV=4.16 kW={power_kw} kvar={kvar}")
                self.bdwpt_loads[bdwpt_name] = power_kw
        else:
            # Simple model - just track the power
            self.bdwpt_loads[bus_id] = power_kw
            
    def solve_power_flow(self):
        """Solve power flow and return results"""
        if USE_OPENDSS:
            # Solve using OpenDSS
            self.dss.solution.solve()
            
            # Get results
            results = self._get_opendss_results()
        else:
            # Simple power flow approximation
            results = self._simple_power_flow()
            
        return results
        
    def _get_opendss_results(self):
        """Extract results from OpenDSS solution"""
        results = {
            'voltages': {},
            'powers': {},
            'losses': 0,
            'converged': self.dss.solution.converged()
        }
        
        # Get bus voltages
        self.dss.circuit.set_active_bus('650')
        for bus in self.buses:
            self.dss.circuit.set_active_bus(str(bus))
            voltages = self.dss.bus.voltages_mag_pu()
            results['voltages'][bus] = np.mean(voltages) if len(voltages) > 0 else 1.0
            
        # Get total power
        results['powers']['total_load'] = self.dss.circuit.total_power()[0]  # Real power
        results['powers']['total_losses'] = self.dss.circuit.losses()[0] / 1000  # kW
        
        return results
        
    def _simple_power_flow(self):
        """Simple power flow calculation without OpenDSS"""
        # Calculate total load
        total_load = sum(load['P'] for load in self.loads.values())
        total_bdwpt = sum(self.bdwpt_loads.values())
        net_load = total_load + total_bdwpt
        
        # Simple voltage drop calculation
        voltage_drop = min(0.1, net_load / 10000)  # Simplified
        
        results = {
            'voltages': {},
            'powers': {
                'total_load': net_load,
                'total_losses': net_load * 0.03  # 3% losses
            },
            'losses': net_load * 0.03,
            'converged': True
        }
        
        # Calculate voltages with simple drop
        for bus in self.buses:
            if bus == 650:  # Slack bus
                results['voltages'][bus] = 1.0
            else:
                # Distance-based voltage drop (simplified)
                distance_factor = (bus - 650) / 100
                results['voltages'][bus] = 1.0 - voltage_drop * distance_factor
                
        return results
        
    def get_voltage(self, bus_id):
        """Get voltage at specific bus"""
        if bus_id in self.voltages:
            return self.voltages[bus_id]
        return 1.0  # Default
        
    def update_voltages(self, results):
        """Update stored voltages from power flow results"""
        self.voltages = results['voltages'].copy()