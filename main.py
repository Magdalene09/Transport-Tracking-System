"""
Main application entry point for the Public Transport Tracking API.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from config import (
    API_TITLE, 
    API_VERSION, 
    API_DESCRIPTION,
    GZIP_MINIMUM_SIZE, 
    LOG_LEVEL, 
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CACHE_CLEANUP_INTERVAL
)
from database import init_db, dispose_db, check_database_connection
from routers import locations, routes, eta, health
from cache import cleanup_expired_cache

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


async def periodic_cache_cleanup():
    """Background task to periodically clean up expired cache entries."""
    while True:
        await asyncio.sleep(CACHE_CLEANUP_INTERVAL)
        try:
            removed = cleanup_expired_cache()
            if removed > 0:
                logger.debug(f"Cache cleanup: {removed} entries removed")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    
    await init_db()
    
    if await check_database_connection():
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection check failed")
    
    cleanup_task = asyncio.create_task(periodic_cache_cleanup())
    logger.info("Background tasks started")
    
    yield
    
    logger.info(f"Shutting down {API_TITLE}")
    
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    await dispose_db()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


app.add_middleware(GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred", "type": type(exc).__name__}
    )


# Include routers
app.include_router(health.router)
app.include_router(locations.router)
app.include_router(routes.router)
app.include_router(eta.router)


@app.get("/", tags=["root"])
async def root():
    """API root endpoint."""
    return {
        "title": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "health": "/health",
            "bus_location": "/bus/{bus_id}/live",
            "bus_routes": "/bus/{bus_number}/routes",
            "bus_eta": "/bus/{bus_number}/eta"
        }
    }


@app.get("/info", tags=["root"])
async def api_info():
    """Get detailed API information."""
    from cache import get_cache_stats
    from database import get_db_stats
    
    return {
        "api": {"title": API_TITLE, "version": API_VERSION},
        "cache": get_cache_stats(),
        "database": await get_db_stats()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

#uvicorn main:app --reload

