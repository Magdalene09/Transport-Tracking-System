"""
Configuration settings for the Public Transport Tracking API.

All configurable values are centralized here for easy management
and can be overridden using environment variables.
"""

import os
from typing import Final

# =============================================================================
# API Configuration
# =============================================================================
API_TITLE: Final[str] = "Public Transport Tracking API"
API_VERSION: Final[str] = "1.0.0"
API_DESCRIPTION: Final[str] = "Real-time public transport tracking system with ETA predictions"

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL: Final[str] = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:root205@localhost:5432/transport_tracking"
)

# Database schema name
SCHEMA_NAME: Final[str] = "transport"

# Connection pool settings
DB_POOL_SIZE: Final[int] = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: Final[int] = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: Final[int] = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# =============================================================================
# Speed Configuration (km/h)
# =============================================================================
DEFAULT_SPEED_KMH: Final[float] = float(os.getenv("DEFAULT_SPEED_KMH", "20.0"))
MIN_SPEED_KMH: Final[float] = float(os.getenv("MIN_SPEED_KMH", "5.0"))
MAX_SPEED_KMH: Final[float] = float(os.getenv("MAX_SPEED_KMH", "80.0"))

# =============================================================================
# Geographic Constants
# =============================================================================
EARTH_RADIUS_KM: Final[float] = 6371.0

# =============================================================================
# Cache Configuration
# =============================================================================
CACHE_TTL_SECONDS: Final[int] = int(os.getenv("CACHE_TTL_SECONDS", "15"))
CACHE_CLEANUP_INTERVAL: Final[int] = int(os.getenv("CACHE_CLEANUP_INTERVAL", "300"))

# =============================================================================
# Middleware Configuration
# =============================================================================
GZIP_MINIMUM_SIZE: Final[int] = int(os.getenv("GZIP_MINIMUM_SIZE", "500"))

# CORS settings
CORS_ORIGINS: Final[list] = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS: Final[bool] = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# Rate Limiting Configuration
# =============================================================================
RATE_LIMIT_ENABLED: Final[bool] = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
RATE_LIMIT_REQUESTS: Final[int] = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_PERIOD: Final[int] = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

# =============================================================================
# ETA Calculation Configuration
# =============================================================================
ETA_BASE_TIME_PER_ROUTE: Final[int] = int(os.getenv("ETA_BASE_TIME_PER_ROUTE", "90"))
ETA_MAX_ADDITIONAL_TIME: Final[int] = int(os.getenv("ETA_MAX_ADDITIONAL_TIME", "180"))
ETA_DEFAULT_STOPPED_MINUTES: Final[int] = int(os.getenv("ETA_DEFAULT_STOPPED_MINUTES", "60"))
