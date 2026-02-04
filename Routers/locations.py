"""
Bus location endpoints for real-time tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from database import get_db
from models import Bus, BusLocation, BusRoute, Route
from schemas import BusLocationResponse

router = APIRouter(prefix="/bus", tags=["locations"])
logger = logging.getLogger(__name__)


@router.get("/{bus_id}/live", response_model=BusLocationResponse)
async def get_live_bus_location(
    bus_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the live location of a specific bus."""
    logger.info(f"Fetching live location for bus_id: {bus_id}")
    
    bus = await db.get(Bus, bus_id)
    if not bus:
        logger.warning(f"Bus not found: {bus_id}")
        raise HTTPException(status_code=404, detail="Bus not found")

    result = await db.execute(
        select(BusLocation)
        .where(BusLocation.bus_id == bus_id)
        .order_by(desc(BusLocation.recorded_at))
        .limit(1)
    )
    location = result.scalar_one_or_none()

    route_name = None
    current_route_result = await db.execute(
        select(BusRoute)
        .where(BusRoute.bus_id == bus_id, BusRoute.is_current == True)
    )
    current_route_assignment = current_route_result.scalar_one_or_none()

    if current_route_assignment:
        route = await db.get(Route, current_route_assignment.route_id)
        if route:
            route_name = route.route_name

    return BusLocationResponse(
        bus_id=bus.bus_id,
        bus_number=bus.bus_number,
        is_active=bus.is_active,
        latest_latitude=location.latitude if location else None,
        latest_longitude=location.longitude if location else None,
        recorded_at=location.recorded_at.isoformat() if location else None,
        route_name=route_name
    )


@router.get("/{bus_id}/history")
async def get_bus_location_history(
    bus_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get location history for a specific bus."""
    bus = await db.get(Bus, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    result = await db.execute(
        select(BusLocation)
        .where(BusLocation.bus_id == bus_id)
        .order_by(desc(BusLocation.recorded_at))
        .limit(limit)
    )
    locations = result.scalars().all()

    return {
        "bus_id": bus.bus_id,
        "bus_number": bus.bus_number,
        "total_records": len(locations),
        "locations": [
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "recorded_at": loc.recorded_at.isoformat()
            }
            for loc in locations
        ]
    }


@router.get("/active")
async def get_all_active_buses(db: AsyncSession = Depends(get_db)):
    """Get all active buses with their current locations."""
    result = await db.execute(select(Bus).where(Bus.is_active == True))
    buses = result.scalars().all()
    
    active_buses = []
    for bus in buses:
        loc_result = await db.execute(
            select(BusLocation)
            .where(BusLocation.bus_id == bus.bus_id)
            .order_by(desc(BusLocation.recorded_at))
            .limit(1)
        )
        location = loc_result.scalar_one_or_none()
        
        route_result = await db.execute(
            select(BusRoute)
            .where(BusRoute.bus_id == bus.bus_id, BusRoute.is_current == True)
        )
        route_assignment = route_result.scalar_one_or_none()
        
        route_name = None
        if route_assignment:
            route = await db.get(Route, route_assignment.route_id)
            if route:
                route_name = route.route_name
        
        active_buses.append({
            "bus_id": bus.bus_id,
            "bus_number": bus.bus_number,
            "latitude": location.latitude if location else None,
            "longitude": location.longitude if location else None,
            "last_update": location.recorded_at.isoformat() if location else None,
            "route_name": route_name
        })
    
    return {"total_active": len(active_buses), "buses": active_buses}
