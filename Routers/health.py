"""
Health check endpoint for the Public Transport Tracking API.
"""

from fastapi import APIRouter
from schemas import HealthResponse
from cache import get_cache_stats
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health status of the API."""
    logger.debug("Health check requested")
    return HealthResponse(status="healthy")


@router.get("/health/detailed")
async def detailed_health_check():
    """Get detailed health information including cache stats."""
    cache_stats = get_cache_stats()
    
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "cache": cache_stats,
        "components": {
            "database": "connected",
            "cache": "active"
        }
    }
