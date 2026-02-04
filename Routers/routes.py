"""
Bus route endpoints for route information and assignments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from database import get_db
from models import Bus, BusRoute, Route, Stop
from schemas import BusRouteInfoResponse

router = APIRouter(prefix="/bus", tags=["routes"])
logger = logging.getLogger(__name__)


@router.get("/{bus_number}/routes", response_model=BusRouteInfoResponse)
async def get_bus_routes(
    bus_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current and previous route assignments for a bus."""
    logger.info(f"Fetching routes for bus: {bus_number}")
    
    result = await db.execute(
        select(Bus).where(Bus.bus_number == bus_number)
    )
    bus = result.scalar_one_or_none()
    
    if not bus:
        logger.warning(f"Bus not found: {bus_number}")
        raise HTTPException(status_code=404, detail="Bus not found")
    
    current_route_result = await db.execute(
        select(BusRoute)
        .where(BusRoute.bus_id == bus.bus_id, BusRoute.is_current == True)
    )
    current_route = current_route_result.scalar_one_or_none()
    
    previous_route = None
    if current_route:
        previous_route_result = await db.execute(
            select(BusRoute)
            .where(
                BusRoute.bus_id == bus.bus_id,
                BusRoute.route_id != current_route.route_id,
                BusRoute.is_current == False
            )
            .order_by(desc(BusRoute.assigned_at))
            .limit(1)
        )
        previous_route = previous_route_result.scalar_one_or_none()
    else:
        route_result = await db.execute(
            select(BusRoute)
            .where(BusRoute.bus_id == bus.bus_id)
            .order_by(desc(BusRoute.assigned_at))
            .limit(2)
        )
        routes = list(route_result.scalars().all())
        if routes:
            current_route = routes[0]
            if len(routes) > 1:
                previous_route = routes[1]
    
    return BusRouteInfoResponse(
        bus_number=bus.bus_number,
        current_route_id=current_route.route_id if current_route else None,
        previous_route_id=previous_route.route_id if previous_route else None
    )


@router.get("/{bus_number}/routes/detailed")
async def get_detailed_bus_routes(
    bus_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed route information including stops for a bus."""
    result = await db.execute(
        select(Bus).where(Bus.bus_number == bus_number)
    )
    bus = result.scalar_one_or_none()
    
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    
    current_route_result = await db.execute(
        select(BusRoute)
        .where(BusRoute.bus_id == bus.bus_id, BusRoute.is_current == True)
    )
    current_route_assignment = current_route_result.scalar_one_or_none()
    
    response_data = {
        "bus_number": bus.bus_number,
        "bus_id": bus.bus_id,
        "is_active": bus.is_active,
        "current_route": None,
        "route_history": []
    }
    
    if current_route_assignment:
        route = await db.get(Route, current_route_assignment.route_id)
        
        stops_result = await db.execute(
            select(Stop)
            .where(Stop.route_id == route.route_id)
            .order_by(Stop.stop_order)
        )
        stops = stops_result.scalars().all()
        
        response_data["current_route"] = {
            "route_id": route.route_id,
            "route_name": route.route_name,
            "route_number": route.route_number,
            "assigned_at": current_route_assignment.assigned_at.isoformat(),
            "stops": [
                {
                    "stop_id": stop.stop_id,
                    "stop_name": stop.stop_name,
                    "stop_order": stop.stop_order,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude
                }
                for stop in stops
            ]
        }
    
    history_result = await db.execute(
        select(BusRoute)
        .where(BusRoute.bus_id == bus.bus_id, BusRoute.is_current == False)
        .order_by(desc(BusRoute.assigned_at))
        .limit(5)
    )
    history = history_result.scalars().all()
    
    for assignment in history:
        route = await db.get(Route, assignment.route_id)
        if route:
            response_data["route_history"].append({
                "route_id": route.route_id,
                "route_name": route.route_name,
                "assigned_at": assignment.assigned_at.isoformat()
            })
    
    return response_data


@router.get("/routes/all")
async def get_all_routes(db: AsyncSession = Depends(get_db)):
    """Get all available routes with their stops."""
    result = await db.execute(select(Route).order_by(Route.route_id))
    routes = result.scalars().all()
    
    routes_data = []
    for route in routes:
        stops_result = await db.execute(
            select(Stop)
            .where(Stop.route_id == route.route_id)
            .order_by(Stop.stop_order)
        )
        stops = stops_result.scalars().all()
        
        routes_data.append({
            "route_id": route.route_id,
            "route_name": route.route_name,
            "route_number": route.route_number,
            "total_stops": len(stops),
            "stops": [{"stop_name": stop.stop_name, "stop_order": stop.stop_order} for stop in stops]
        })
    
    return {"total_routes": len(routes_data), "routes": routes_data}
