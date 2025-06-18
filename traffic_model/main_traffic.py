# traffic_model/main_traffic.py - Traffic simulation module

import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class TrafficModel:
    """Traffic model for simulating vehicle movements and EV distribution"""
    
    def __init__(self, config):
        self.config = config
        self.vehicles = []
        self.road_segments = []
        self.initialize_road_network()
        self.initialize_vehicles()
        
    def initialize_road_network(self):
        """Initialize road network corresponding to power grid nodes"""
        # Create road segments that correspond to IEEE 13-bus nodes
        self.road_segments = []
        
        # Map power nodes to road segments
        for node in self.config.grid_params['bdwpt_nodes']:
            segment = {
                'id': f'road_{node}',
                'power_node': node,
                'length_km': np.random.uniform(0.5, 2.0),  # Random road length
                'has_bdwpt': True,
                'traffic_capacity': np.random.randint(50, 200),  # Vehicles per hour
                'current_vehicles': []
            }
            self.road_segments.append(segment)
            
        logger.info(f"Initialized {len(self.road_segments)} road segments with BDWPT")
        
    def initialize_vehicles(self):
        """Initialize vehicle population with EVs"""
        total_vehicles = self.config.traffic_params['total_vehicles']
        ev_count = int(total_vehicles * self.config.traffic_params['ev_penetration'])
        
        self.vehicles = []
        
        for i in range(total_vehicles):
            is_ev = i < ev_count
            
            vehicle = {
                'id': i,
                'type': 'EV' if is_ev else 'ICE',
                'is_bdwpt_equipped': False,  # Will be set based on scenario
                'battery_capacity': self.config.ev_params['battery_capacity_kwh'] if is_ev else 0,
                'current_soc': 0,
                'location': None,
                'status': 'parked',  # parked, driving
                'trip_chain': [],
                'energy_consumed': 0
            }
            
            if is_ev:
                # Initialize SoC from normal distribution
                vehicle['current_soc'] = np.clip(
                    np.random.normal(
                        self.config.ev_params['initial_soc_mean'],
                        self.config.ev_params['initial_soc_std']
                    ),
                    0.1, 1.0
                )
                
            self.vehicles.append(vehicle)
            
        logger.info(f"Initialized {total_vehicles} vehicles ({ev_count} EVs)")
        
    def generate_trip_patterns(self, time_of_day_hour, day_type='weekday'):
        """Generate trip patterns based on time of day"""
        # Trip generation rate based on time of day
        base_rate = self.config.traffic_params['trips_per_vehicle_per_day'] / 24
        
        # Peak hour multipliers
        if day_type == 'weekday':
            if 7 <= time_of_day_hour < 9:  # Morning peak
                rate_multiplier = 3.0
            elif 17 <= time_of_day_hour < 19:  # Evening peak
                rate_multiplier = 2.5
            elif 9 <= time_of_day_hour < 17:  # Daytime
                rate_multiplier = 1.2
            else:  # Night
                rate_multiplier = 0.3
        else:  # Weekend
            if 10 <= time_of_day_hour < 20:  # Daytime
                rate_multiplier = 1.5
            else:
                rate_multiplier = 0.5
                
        trip_rate = base_rate * rate_multiplier
        
        # Generate trips for vehicles
        trips = []
        for vehicle in self.vehicles:
            if vehicle['status'] == 'parked' and np.random.random() < trip_rate:
                # Generate a trip
                trip = self.generate_single_trip(vehicle)
                trips.append(trip)
                vehicle['status'] = 'driving'
                
        return trips
        
    def generate_single_trip(self, vehicle):
        """Generate a single trip for a vehicle"""
        # Select random origin and destination road segments
        origin = np.random.choice(self.road_segments)
        destination = np.random.choice(self.road_segments)
        
        # Trip distance (log-normal distribution)
        distance_km = np.clip(
            np.random.lognormal(
                np.log(self.config.traffic_params['average_trip_distance_km']),
                0.5
            ),
            1.0, 50.0  # Min 1km, max 50km
        )
        
        # Trip duration (assuming average speed of 30 km/h in urban area)
        duration_minutes = distance_km / 30 * 60
        
        trip = {
            'vehicle_id': vehicle['id'],
            'origin': origin['id'],
            'destination': destination['id'],
            'distance_km': distance_km,
            'duration_minutes': duration_minutes,
            'start_time': None,  # Will be set by simulation engine
            'path': self.calculate_path(origin, destination)
        }
        
        return trip
        
    def calculate_path(self, origin, destination):
        """Calculate path between origin and destination (simplified)"""
        # For simplicity, assume vehicles pass through intermediate BDWPT segments
        path = [origin['id']]
        
        # Add some intermediate segments
        available_segments = [s for s in self.road_segments 
                            if s['id'] not in [origin['id'], destination['id']]]
        
        if len(available_segments) > 0:
            num_intermediate = min(2, len(available_segments))
            intermediate = np.random.choice(available_segments, num_intermediate, replace=False)
            path.extend([s['id'] for s in intermediate])
            
        path.append(destination['id'])
        
        return path
        
    def update_vehicle_positions(self, current_time_step):
        """Update vehicle positions based on ongoing trips"""
        vehicles_on_roads = {segment['id']: [] for segment in self.road_segments}
        
        for vehicle in self.vehicles:
            if vehicle['status'] == 'driving' and len(vehicle['trip_chain']) > 0:
                current_trip = vehicle['trip_chain'][0]
                
                # Simple position update - place vehicle on current road segment
                progress = min(1.0, current_time_step / current_trip['duration_minutes'])
                
                if progress < 1.0:
                    # Vehicle still traveling
                    path_index = int(progress * (len(current_trip['path']) - 1))
                    current_road = current_trip['path'][path_index]
                    vehicle['location'] = current_road
                    vehicles_on_roads[current_road].append(vehicle['id'])
                    
                    # Update energy consumption for EVs
                    if vehicle['type'] == 'EV':
                        distance_this_step = (current_trip['distance_km'] / 
                                            current_trip['duration_minutes'] * 
                                            self.config.time_step_minutes)
                        energy_consumed = (distance_this_step * 
                                         self.config.ev_params['energy_consumption_kwh_per_km'])
                        vehicle['energy_consumed'] += energy_consumed
                        
                else:
                    # Trip completed
                    vehicle['status'] = 'parked'
                    vehicle['trip_chain'].pop(0)
                    vehicle['location'] = current_trip['destination']
                    
        return vehicles_on_roads
        
    def get_bdwpt_vehicles_by_node(self, power_node):
        """Get BDWPT-equipped vehicles at a specific power node"""
        # Find corresponding road segment
        road_segment = next((s for s in self.road_segments 
                           if s['power_node'] == power_node), None)
        
        if not road_segment:
            return []
            
        # Get vehicles on this road segment
        vehicles_here = [v for v in self.vehicles 
                        if v['location'] == road_segment['id'] and 
                        v['is_bdwpt_equipped'] and
                        v['type'] == 'EV']
        
        return vehicles_here
        
    def set_bdwpt_penetration(self, penetration_percent):
        """Set BDWPT equipment penetration for EVs"""
        evs = [v for v in self.vehicles if v['type'] == 'EV']
        num_bdwpt = int(len(evs) * penetration_percent / 100)
        
        # Randomly select EVs to equip with BDWPT
        bdwpt_evs = np.random.choice(evs, num_bdwpt, replace=False)
        
        for vehicle in self.vehicles:
            vehicle['is_bdwpt_equipped'] = vehicle in bdwpt_evs
            
        logger.info(f"Set BDWPT penetration to {penetration_percent}% ({num_bdwpt} vehicles)")


# traffic_model/trip_generator.py
class TripGenerator:
    """Generate realistic trip patterns for vehicles"""
    
    def __init__(self, config):
        self.config = config
        
    def generate_daily_trips(self, num_vehicles, day_type='weekday'):
        """Generate full day trip chains for vehicles"""
        all_trips = []
        
        # Trip purpose probabilities
        trip_purposes = {
            'home_work': 0.35,
            'work_home': 0.25,
            'shopping': 0.15,
            'leisure': 0.15,
            'other': 0.10
        }
        
        for vehicle_id in range(num_vehicles):
            daily_trips = self.generate_vehicle_trip_chain(vehicle_id, day_type, trip_purposes)
            all_trips.extend(daily_trips)
            
        return all_trips
        
    def generate_vehicle_trip_chain(self, vehicle_id, day_type, trip_purposes):
        """Generate trip chain for a single vehicle"""
        trips = []
        
        # Number of trips (Poisson distribution)
        num_trips = np.random.poisson(self.config.traffic_params['trips_per_vehicle_per_day'])
        num_trips = max(0, min(num_trips, 6))  # Limit to reasonable range
        
        current_location = 'home'
        current_time = 0  # Minutes since midnight
        
        for i in range(num_trips):
            # Select trip purpose
            purpose = np.random.choice(
                list(trip_purposes.keys()),
                p=list(trip_purposes.values())
            )
            
            # Determine destination based on purpose
            if purpose == 'home_work':
                destination = 'work'
                preferred_time = 7.5 * 60  # 7:30 AM
            elif purpose == 'work_home':
                destination = 'home'
                preferred_time = 17.5 * 60  # 5:30 PM
            else:
                destination = purpose
                preferred_time = current_time + np.random.uniform(30, 180)
                
            # Add some randomness to departure time
            departure_time = max(current_time, 
                               preferred_time + np.random.normal(0, 30))
            
            trip = {
                'vehicle_id': vehicle_id,
                'trip_id': i,
                'purpose': purpose,
                'origin': current_location,
                'destination': destination,
                'departure_time': departure_time,
                'distance_km': self.sample_trip_distance(purpose)
            }
            
            trips.append(trip)
            current_location = destination
            current_time = departure_time + trip['distance_km'] / 30 * 60  # Assume 30 km/h
            
        return trips
        
    def sample_trip_distance(self, purpose):
        """Sample trip distance based on purpose"""
        # Distance distributions by purpose (km)
        distance_params = {
            'home_work': (12, 5),     # mean, std
            'work_home': (12, 5),
            'shopping': (5, 2),
            'leisure': (8, 4),
            'other': (6, 3)
        }
        
        mean, std = distance_params.get(purpose, (8, 4))
        distance = np.random.normal(mean, std)
        return max(1.0, min(distance, 50.0))  # Clamp to reasonable range


# traffic_model/vehicle_movement.py
class VehicleMovement:
    """Handle vehicle movement simulation on road network"""
    
    def __init__(self, road_network):
        self.road_network = road_network
        self.vehicle_positions = {}
        
    def update_positions(self, vehicles, trips, current_time):
        """Update vehicle positions based on active trips"""
        active_vehicles = {}
        
        for trip in trips:
            if trip['departure_time'] <= current_time <= trip['arrival_time']:
                progress = (current_time - trip['departure_time']) / trip['duration']
                position = self.interpolate_position(trip, progress)
                active_vehicles[trip['vehicle_id']] = position
                
        return active_vehicles
        
    def interpolate_position(self, trip, progress):
        """Interpolate vehicle position along trip path"""
        path_segments = trip['path']
        total_segments = len(path_segments) - 1
        
        if total_segments == 0:
            return path_segments[0]
            
        segment_progress = progress * total_segments
        segment_index = int(segment_progress)
        
        if segment_index >= total_segments:
            return path_segments[-1]
            
        return path_segments[segment_index]