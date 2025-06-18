# /1_traffic_model/vehicle_movement.py

import numpy as np
import logging

logger = logging.getLogger(__name__)

class VehicleMovement:
    """Handles vehicle movement simulation on the road network."""

    def __init__(self, road_network, config):
        """
        Initializes the VehicleMovement simulator.

        Args:
            road_network (list): A list of road segment dictionaries.
            config (SimulationConfig): The main configuration object.
        """
        self.road_network = road_network
        self.config = config
        self.vehicle_positions = {} # Stores current segment_id for each vehicle

    def update_positions(self, vehicles, trips, current_time_minutes):
        """
        Updates vehicle positions based on active trips for the current time step.
        """
        # Reset all vehicle statuses before updating
        for v in vehicles:
            if v['status'] == 'driving':
                v['status'] = 'parked'

        active_trips = trips[
            (trips['departure_time'] <= current_time_minutes) &
            (trips['arrival_time'] > current_time_minutes)
        ]

        for _, trip in active_trips.iterrows():
            vehicle_id = trip['vehicle_id']
            destination_node = trip['destination']
            
            if 0 <= vehicle_id < len(vehicles) and destination_node != 'home':
                # Update vehicle's status and location
                vehicles[vehicle_id]['status'] = 'driving'
                # FIX: Assign the raw destination node ID as the location
                vehicles[vehicle_id]['location'] = destination_node
                logger.debug(f"Vehicle {vehicle_id} is active on trip to node {destination_node}. Location set.")

        # Update status for vehicles that just finished a trip
        finished_trips = trips[trips['arrival_time'] == current_time_minutes]
        for _, trip in finished_trips.iterrows():
            vehicle_id = trip['vehicle_id']
            if 0 <= vehicle_id < len(vehicles):
                vehicles[vehicle_id]['status'] = 'parked'
                vehicles[vehicle_id]['location'] = trip['destination']
                logger.debug(f"Vehicle {vehicle_id} finished trip. Location parked at {trip['destination']}.")

        # This part is not critical for the bug but kept for structure.
        vehicles_on_segments = {}
        return vehicles_on_segments