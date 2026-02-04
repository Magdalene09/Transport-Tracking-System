"""
Utility functions for the Public Transport Tracking API.
"""

import math
from typing import List, Optional
from datetime import datetime
import logging

from models import Stop, BusLocation
from config import (
    EARTH_RADIUS_KM, 
    DEFAULT_SPEED_KMH, 
    MIN_SPEED_KMH, 
    MAX_SPEED_KMH
)

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
        
    Returns:
        Distance in kilometers
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the initial bearing from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    
    return (bearing + 360) % 360


def calculate_speed_kmh(
    prev_lat: float, 
    prev_lon: float, 
    prev_time: datetime,
    curr_lat: float, 
    curr_lon: float, 
    curr_time: datetime
) -> float:
    """Calculate speed in km/h between two location points."""
    time_delta_seconds = (curr_time - prev_time).total_seconds()
    
    if time_delta_seconds <= 0:
        return DEFAULT_SPEED_KMH
    
    distance_km = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
    speed_kmh = (distance_km / time_delta_seconds) * 3600
    
    return max(MIN_SPEED_KMH, min(MAX_SPEED_KMH, speed_kmh))


def compute_rolling_average_speed(locations: List[BusLocation]) -> float:
    """Compute the rolling average speed from a list of location points."""
    if len(locations) < 2:
        return DEFAULT_SPEED_KMH
    
    locations_chrono = list(reversed(locations))
    speeds = []
    
    for i in range(1, len(locations_chrono)):
        speed = calculate_speed_kmh(
            locations_chrono[i-1].latitude,
            locations_chrono[i-1].longitude,
            locations_chrono[i-1].recorded_at,
            locations_chrono[i].latitude,
            locations_chrono[i].longitude,
            locations_chrono[i].recorded_at
        )
        speeds.append(speed)
    
    if not speeds:
        return DEFAULT_SPEED_KMH
    
    return sum(speeds) / len(speeds)


def find_next_stop_index(
    stops: List[Stop], 
    current_lat: float, 
    current_lon: float
) -> int:
    """Find the index of the next stop based on current position."""
    if not stops:
        return 0
    
    min_distance = float('inf')
    closest_index = 0
    
    for i, stop in enumerate(stops):
        distance = haversine_distance(
            current_lat, 
            current_lon, 
            stop.latitude, 
            stop.longitude
        )
        if distance < min_distance:
            min_distance = distance
            closest_index = i
    
    return closest_index


def find_stop_by_order(stops: List[Stop], stop_order: int) -> Optional[Stop]:
    """Find a stop by its stop_order value."""
    for stop in stops:
        if stop.stop_order == stop_order:
            return stop
    return None


def calculate_route_distance_to_stop(
    stops: List[Stop],
    target_stop_index: int,
    current_lat: float,
    current_lon: float
) -> float:
    """Calculate the total route distance to a target stop."""
    if target_stop_index >= len(stops) or not stops:
        return 0.0
    
    current_stop_index = find_next_stop_index(stops, current_lat, current_lon)
    
    if current_stop_index >= target_stop_index:
        return haversine_distance(
            current_lat, current_lon,
            stops[target_stop_index].latitude,
            stops[target_stop_index].longitude
        )
    
    total_distance = 0.0
    prev_lat, prev_lon = current_lat, current_lon
    
    for i in range(current_stop_index, target_stop_index + 1):
        distance = haversine_distance(
            prev_lat, prev_lon,
            stops[i].latitude, stops[i].longitude
        )
        total_distance += distance
        prev_lat, prev_lon = stops[i].latitude, stops[i].longitude
    
    return total_distance


def format_distance(distance_km: float) -> str:
    """Format distance for display."""
    if distance_km < 1:
        return f"{int(distance_km * 1000)} m"
    elif distance_km < 10:
        return f"{distance_km:.1f} km"
    else:
        return f"{int(distance_km)} km"


def estimate_arrival_time(distance_km: float, speed_kmh: float) -> int:
    """Estimate arrival time in minutes."""
    if speed_kmh <= 0:
        return 60
    
    eta_hours = distance_km / speed_kmh
    eta_minutes = int(eta_hours * 60)
    
    return max(1, eta_minutes)


def is_bus_approaching(
    prev_lat: float,
    prev_lon: float,
    curr_lat: float,
    curr_lon: float,
    stop_lat: float,
    stop_lon: float
) -> bool:
    """Determine if a bus is approaching a stop."""
    prev_distance = haversine_distance(prev_lat, prev_lon, stop_lat, stop_lon)
    curr_distance = haversine_distance(curr_lat, curr_lon, stop_lat, stop_lon)
    
    return curr_distance < prev_distance
