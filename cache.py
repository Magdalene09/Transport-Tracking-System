from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple, Any
import logging

from config import CACHE_TTL_SECONDS
from schemas import ETAResponse

logger = logging.getLogger(__name__)

# Maximum entries allowed in each cache
MAX_CACHE_SIZE = 25

# Least recently used entry is at the beginning
# Most recently used entry is at the end
eta_cache: OrderedDict[str, Tuple[List[ETAResponse], datetime]] = OrderedDict()
general_cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()


def get_cache_key(stop_id: int) -> str:
    """Generate a cache key for a stop ID."""
    return f"eta_{stop_id}"


def get_bus_cache_key(bus_number: str, route_id: int) -> str:
    """Generate a cache key for bus ETA."""
    return f"bus_eta_{bus_number}_{route_id}"


def _get_cached_data(cache: OrderedDict, cache_key: str) -> Optional[Any]:
    """Retrieve valid data and mark it as most recently used."""

    if cache_key not in cache:
        return None

    cached_data, cached_time = cache[cache_key]

    age_seconds = (
        datetime.now(timezone.utc) - cached_time
    ).total_seconds()

    # Remove expired entries
    if age_seconds >= CACHE_TTL_SECONDS:
        del cache[cache_key]
        logger.debug(f"Expired cache entry: {cache_key}")
        return None

    # Mark this entry as most recently used
    cache.move_to_end(cache_key)

    logger.debug(f"Cache hit for {cache_key}")
    return cached_data


def _set_cached_data(
    cache: OrderedDict,
    cache_key: str,
    data: Any
) -> None:
    """Insert or update data and evict the least recently used entry."""

    # Remove existing entry before reinserting it as most recently used
    cache.pop(cache_key, None)

    # Insert at the most recently used position
    cache[cache_key] = (data, datetime.now(timezone.utc))

    # Evict the least recently used entry if capacity is exceeded
    if len(cache) > MAX_CACHE_SIZE:
        evicted_key, _ = cache.popitem(last=False)
        logger.debug(f"LRU eviction: {evicted_key}")


def get_cached_eta(stop_id: int) -> Optional[List[ETAResponse]]:
    """Retrieve cached ETA data for a stop."""
    cache_key = get_cache_key(stop_id)
    return _get_cached_data(eta_cache, cache_key)


def set_cached_eta(stop_id: int, data: List[ETAResponse]) -> None:
    """Store ETA data in the LRU cache."""
    cache_key = get_cache_key(stop_id)
    _set_cached_data(eta_cache, cache_key, data)


def get_cached_bus_eta(bus_number: str, route_id: int) -> Optional[Dict]:
    """Retrieve cached bus ETA data."""
    cache_key = get_bus_cache_key(bus_number, route_id)
    return _get_cached_data(general_cache, cache_key)


def set_cached_bus_eta(
    bus_number: str,
    route_id: int,
    data: Dict
) -> None:
    """Store bus ETA data in the LRU cache."""
    cache_key = get_bus_cache_key(bus_number, route_id)
    _set_cached_data(general_cache, cache_key, data)


def clear_eta_cache() -> None:
    """Clear all ETA cache entries."""
    cache_keys_to_clear = [
        key for key in eta_cache if key.startswith("eta_")
    ]

    for key in cache_keys_to_clear:
        del eta_cache[key]

    logger.info(f"Cleared {len(cache_keys_to_clear)} ETA cache entries")


def clear_all_cache() -> None:
    """Clear all cache entries."""
    eta_cache.clear()
    general_cache.clear()
    logger.info("Cleared all cache entries")


def cleanup_expired_cache() -> int:
    """Remove expired entries from both caches."""

    now = datetime.now(timezone.utc)
    removed_count = 0

    for cache in (eta_cache, general_cache):
        expired_keys = [
            key
            for key, (_, cached_time) in cache.items()
            if (now - cached_time).total_seconds() >= CACHE_TTL_SECONDS
        ]

        for key in expired_keys:
            del cache[key]
            removed_count += 1

    return removed_count


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""

    return {
        "eta_cache_entries": len(eta_cache),
        "general_cache_entries": len(general_cache),
        "total_entries": len(eta_cache) + len(general_cache),
        "ttl_seconds": CACHE_TTL_SECONDS,
        "max_cache_size_per_cache": MAX_CACHE_SIZE
    }
