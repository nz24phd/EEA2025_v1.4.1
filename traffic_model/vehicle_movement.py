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

        Args:
            vehicles (list): The list of all vehicle dictionaries.
            trips (pd.DataFrame): The DataFrame of all generated daily trips.
            current_time_minutes (int): The current time in minutes since midnight.

        Returns:
            dict: A dictionary mapping road segment IDs to a list of vehicle IDs currently on that segment.
        """
        vehicles_on_segments = {segment['id']: [] for segment in self.road_network}

        # Reset all vehicle statuses before updating
        for v in vehicles:
            if v['status'] == 'driving': # Only reset driving cars to parked, others stay parked
                v['status'] = 'parked'

        active_trips = trips[
            (trips['departure_time'] <= current_time_minutes) &
            (trips['arrival_time'] > current_time_minutes)
        ]

        for _, trip in active_trips.iterrows():
            vehicle_id = trip['vehicle_id']
            # For this simulation, we assume the vehicle's load is applied at the destination node for the trip's duration.
            destination_segment_id = f"road_node_{trip['destination']}"
            
            if 0 <= vehicle_id < len(vehicles):
                # Update vehicle's main status
                vehicles[vehicle_id]['status'] = 'driving'
                vehicles[vehicle_id]['location'] = destination_segment_id

                if destination_segment_id in vehicles_on_segments:
                    vehicles_on_segments[destination_segment_id].append(vehicle_id)

        # Update status for vehicles that just finished a trip
        finished_trips = trips[trips['arrival_time'] == current_time_minutes]
        for _, trip in finished_trips.iterrows():
            vehicle_id = trip['vehicle_id']
            if 0 <= vehicle_id < len(vehicles):
                vehicles[vehicle_id]['status'] = 'parked'
                vehicles[vehicle_id]['location'] = trip['destination'] # Or home base

        return vehicles_on_segments