"""
ETA calculation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from database import get_db
from models import Bus, BusRoute, Route, Stop, BusLocation
from schemas import BusETAResponse
from utils import haversine_distance, compute_rolling_average_speed, find_next_stop_index
from cache import get_cached_bus_eta, set_cached_bus_eta

router = APIRouter(prefix="/bus", tags=["eta"])
logger = logging.getLogger(__name__)


def format_eta_time(eta_minutes: int) -> str:
    """Format ETA minutes into human-readable string."""
    if eta_minutes < 60:
        time_unit = f"{eta_minutes} minute{'s' if eta_minutes != 1 else ''}"
    elif eta_minutes < 1440:
        hours = eta_minutes // 60
        remaining_minutes = eta_minutes % 60
        if remaining_minutes > 0:
            time_unit = f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} min"
        else:
            time_unit = f"{hours} hour{'s' if hours != 1 else ''}"
    elif eta_minutes < 10080:
        days = eta_minutes // 1440
        time_unit = f"{days} day{'s' if days != 1 else ''}"
    else:
        weeks = eta_minutes // 10080
        time_unit = f"{weeks} week{'s' if weeks != 1 else ''}"
    
    return f"Estimated arrival time: {time_unit}"


async def get_bus_by_number(db: AsyncSession, bus_number: str) -> Bus:
    """Retrieve bus by bus number."""
    bus_result = await db.execute(
        select(Bus).where(Bus.bus_number == bus_number)
    )
    bus = bus_result.scalar_one_or_none()
    
    if not bus:
        logger.warning(f"Bus not found: {bus_number}")
        raise HTTPException(status_code=404, detail="Bus not found")
    
    return bus


async def get_current_route_assignment(db: AsyncSession, bus_id: int) -> BusRoute:
    """Get the current route assignment for a bus."""
    current_route_result = await db.execute(
        select(BusRoute)
        .where(BusRoute.bus_id == bus_id, BusRoute.is_current == True)
    )
    current_route_assignment = current_route_result.scalar_one_or_none()
    
    if not current_route_assignment:
        raise HTTPException(status_code=400, detail="Bus not assigned to any route")
    
    return current_route_assignment


async def get_route_stops(db: AsyncSession, route_id: int) -> list:
    """Get all stops for a route ordered by stop_order."""
    stops_result = await db.execute(
        select(Stop)
        .where(Stop.route_id == route_id)
        .order_by(Stop.stop_order)
    )
    stops = list(stops_result.scalars().all())
    
    if not stops:
        raise HTTPException(status_code=400, detail="Route has no stops")
    
    return stops


async def get_bus_locations(db: AsyncSession, bus_id: int, limit: int = 10) -> list:
    """Get recent locations for a bus."""
    locations_result = await db.execute(
        select(BusLocation)
        .where(BusLocation.bus_id == bus_id)
        .order_by(desc(BusLocation.recorded_at))
        .limit(limit)
    )
    locations = list(locations_result.scalars().all())
    
    if not locations:
        raise HTTPException(status_code=400, detail="No location data for bus")
    
    return locations


def calculate_eta_same_route(stops: list, locations: list, target_stop_index: int = None) -> int:
    """Calculate ETA when bus is on the same route as user."""
    avg_speed_kmh = compute_rolling_average_speed(locations)
    current_location = locations[0]
    
    next_stop_index = find_next_stop_index(
        stops,
        current_location.latitude,
        current_location.longitude
    )
    
    if target_stop_index is not None and target_stop_index < len(stops):
        target_stop = stops[target_stop_index]
    elif next_stop_index + 1 < len(stops):
        target_stop = stops[next_stop_index + 1]
    else:
        target_stop = stops[next_stop_index] if next_stop_index < len(stops) else stops[0]
    
    distance_to_next_stop_km = haversine_distance(
        current_location.latitude,
        current_location.longitude,
        target_stop.latitude,
        target_stop.longitude
    )
    
    if avg_speed_kmh > 0:
        eta_minutes = max(1, int((distance_to_next_stop_km / avg_speed_kmh) * 60))
    else:
        eta_minutes = 60
    
    return eta_minutes


def calculate_eta_different_route(route_difference: int) -> int:
    """Calculate ETA when bus is on a different route."""
    base_time_per_route = 90
    additional_time = min(route_difference * 30, 180)
    return (route_difference * base_time_per_route) + additional_time


@router.get("/{bus_number}/eta", response_model=BusETAResponse)
async def get_bus_eta(
    bus_number: str,
    route_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Calculate the estimated time of arrival for a bus."""
    logger.info(f"Calculating ETA for bus {bus_number} to route {route_id}")
    
    # Check cache first
    cached = get_cached_bus_eta(bus_number, route_id)
    if cached:
        logger.debug(f"Returning cached ETA for {bus_number}")
        return BusETAResponse(**cached)
    
    bus = await get_bus_by_number(db, bus_number)
    current_route_assignment = await get_current_route_assignment(db, bus.bus_id)
    current_route_id = current_route_assignment.route_id
    
    route_difference = abs(route_id - current_route_id)
    
    if route_difference == 0:
        route = await db.get(Route, current_route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        
        stops = await get_route_stops(db, route.route_id)
        locations = await get_bus_locations(db, bus.bus_id)
        
        eta_minutes = calculate_eta_same_route(stops, locations)
    else:
        eta_minutes = calculate_eta_different_route(route_difference)
    
    estimated_arrival_time = format_eta_time(eta_minutes)
    
    result = {
        "bus_number": bus.bus_number,
        "estimated_arrival_time": estimated_arrival_time,
        "current_route_id": current_route_id
    }
    
    # Cache the result
    set_cached_bus_eta(bus_number, route_id, result)
    
    return BusETAResponse(**result)


@router.get("/{bus_number}/eta/detailed")
async def get_detailed_bus_eta(
    bus_number: str,
    route_id: int,
    stop_order: int = None,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed ETA information including distance and speed."""
    bus = await get_bus_by_number(db, bus_number)
    current_route_assignment = await get_current_route_assignment(db, bus.bus_id)
    current_route_id = current_route_assignment.route_id
    
    route_difference = abs(route_id - current_route_id)
    
    response_data = {
        "bus_number": bus.bus_number,
        "bus_id": bus.bus_id,
        "is_active": bus.is_active,
        "current_route_id": current_route_id,
        "requested_route_id": route_id,
        "route_difference": route_difference
    }
    
    if route_difference == 0:
        route = await db.get(Route, current_route_id)
        stops = await get_route_stops(db, route.route_id)
        locations = await get_bus_locations(db, bus.bus_id)
        
        current_location = locations[0]
        avg_speed_kmh = compute_rolling_average_speed(locations)
        
        target_stop_index = None
        if stop_order is not None:
            for i, stop in enumerate(stops):
                if stop.stop_order == stop_order:
                    target_stop_index = i
                    break
        
        if target_stop_index is None:
            next_stop_index = find_next_stop_index(stops, current_location.latitude, current_location.longitude)
            target_stop_index = min(next_stop_index + 1, len(stops) - 1)
        
        target_stop = stops[target_stop_index]
        
        distance_km = haversine_distance(
            current_location.latitude,
            current_location.longitude,
            target_stop.latitude,
            target_stop.longitude
        )
        
        eta_minutes = calculate_eta_same_route(stops, locations, target_stop_index)
        
        response_data.update({
            "route_name": route.route_name,
            "current_latitude": current_location.latitude,
            "current_longitude": current_location.longitude,
            "target_stop_name": target_stop.stop_name,
            "target_stop_order": target_stop.stop_order,
            "distance_km": round(distance_km, 2),
            "average_speed_kmh": round(avg_speed_kmh, 1),
            "eta_minutes": eta_minutes,
            "estimated_arrival_time": format_eta_time(eta_minutes),
            "total_stops_on_route": len(stops)
        })
    else:
        eta_minutes = calculate_eta_different_route(route_difference)
        response_data.update({
            "eta_minutes": eta_minutes,
            "estimated_arrival_time": format_eta_time(eta_minutes),
            "note": "Bus is on a different route"
        })
    
    return response_data
