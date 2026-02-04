"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


class LocationUpdate(BaseModel):
    """Schema for updating bus location."""
    bus_id: int = Field(..., ge=1, description="Bus ID (must be positive)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    timestamp: Optional[datetime] = Field(None, description="Location timestamp (UTC)")

    class Config:
        json_schema_extra = {
            "example": {
                "bus_id": 1,
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        }


class BusLocationResponse(BaseModel):
    """Response schema for bus location queries."""
    bus_id: int
    bus_number: str
    is_active: bool
    latest_latitude: Optional[float] = None
    latest_longitude: Optional[float] = None
    recorded_at: Optional[str] = None
    route_name: Optional[str] = None


class BusOnRouteResponse(BaseModel):
    """Response schema for buses on a specific route."""
    bus_id: int
    bus_number: str
    is_active: bool
    latest_latitude: Optional[float] = None
    latest_longitude: Optional[float] = None
    recorded_at: Optional[str] = None


class ETAResponse(BaseModel):
    """Detailed ETA response with calculation metrics."""
    bus_id: int
    bus_number: str
    distance_km: float = Field(..., ge=0)
    speed_kmh: float = Field(..., ge=0)
    eta_minutes: int = Field(..., ge=0)


class BusRouteInfoResponse(BaseModel):
    """Response schema for bus route information."""
    bus_number: str
    current_route_id: Optional[int] = None
    previous_route_id: Optional[int] = None


class BusETAResponse(BaseModel):
    """Response schema for bus ETA queries."""
    bus_number: str
    estimated_arrival_time: str
    current_route_id: int


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str


class StopInfo(BaseModel):
    """Schema for stop information."""
    stop_id: int
    stop_name: str
    stop_order: int
    latitude: float
    longitude: float


class RouteDetailResponse(BaseModel):
    """Detailed route information with stops."""
    route_id: int
    route_name: str
    route_number: Optional[str]
    stops: List[StopInfo]


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str
    type: Optional[str] = None
