"""
Caching utilities for ETA and frequently accessed data.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Any
import logging

from config import CACHE_TTL_SECONDS
from schemas import ETAResponse

logger = logging.getLogger(__name__)

# Cache storage
eta_cache: Dict[str, Tuple[List[ETAResponse], datetime]] = {}
general_cache: Dict[str, Tuple[Any, datetime]] = {}


def get_cache_key(stop_id: int) -> str:
    """Generate a cache key for a stop ID."""
    return f"eta_{stop_id}"


def get_bus_cache_key(bus_number: str, route_id: int) -> str:
    """Generate a cache key for bus ETA."""
    return f"bus_eta_{bus_number}_{route_id}"


def get_cached_eta(stop_id: int) -> Optional[List[ETAResponse]]:
    """Retrieve cached ETA data for a stop."""
    cache_key = get_cache_key(stop_id)
    
    if cache_key in eta_cache:
        cached_data, cached_time = eta_cache[cache_key]
        age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
        
        if age_seconds < CACHE_TTL_SECONDS:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
        
        del eta_cache[cache_key]
    
    return None


def set_cached_eta(stop_id: int, data: List[ETAResponse]) -> None:
    """Store ETA data in cache."""
    cache_key = get_cache_key(stop_id)
    eta_cache[cache_key] = (data, datetime.now(timezone.utc))
    logger.debug(f"Cached data for {cache_key}")


def get_cached_bus_eta(bus_number: str, route_id: int) -> Optional[Dict]:
    """Retrieve cached bus ETA data."""
    cache_key = get_bus_cache_key(bus_number, route_id)
    
    if cache_key in general_cache:
        cached_data, cached_time = general_cache[cache_key]
        age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
        
        if age_seconds < CACHE_TTL_SECONDS:
            return cached_data
        
        del general_cache[cache_key]
    
    return None


def set_cached_bus_eta(bus_number: str, route_id: int, data: Dict) -> None:
    """Store bus ETA data in cache."""
    cache_key = get_bus_cache_key(bus_number, route_id)
    general_cache[cache_key] = (data, datetime.now(timezone.utc))


def clear_eta_cache() -> None:
    """Clear all ETA-related cache entries."""
    cache_keys_to_clear = [key for key in eta_cache.keys() if key.startswith("eta_")]
    for key in cache_keys_to_clear:
        del eta_cache[key]
    logger.info(f"Cleared {len(cache_keys_to_clear)} ETA cache entries")


def clear_all_cache() -> None:
    """Clear all cache entries."""
    eta_cache.clear()
    general_cache.clear()
    logger.info("Cleared all cache entries")


def cleanup_expired_cache() -> int:
    """Remove expired entries from all caches."""
    now = datetime.now(timezone.utc)
    removed_count = 0
    
    expired_keys = [
        key for key, (_, cached_time) in eta_cache.items()
        if (now - cached_time).total_seconds() >= CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        del eta_cache[key]
        removed_count += 1
    
    expired_keys = [
        key for key, (_, cached_time) in general_cache.items()
        if (now - cached_time).total_seconds() >= CACHE_TTL_SECONDS
    ]
    for key in expired_keys:
        del general_cache[key]
        removed_count += 1
    
    return removed_count


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about the cache."""
    return {
        "eta_cache_entries": len(eta_cache),
        "general_cache_entries": len(general_cache),
        "total_entries": len(eta_cache) + len(general_cache),
        "ttl_seconds": CACHE_TTL_SECONDS
    }
