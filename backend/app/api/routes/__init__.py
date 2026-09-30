"""API routes package for AgriSense AI."""

from app.api.routes.weather import router as weather_router
from app.api.routes.satellite import router as satellite_router
from app.api.routes.soil import router as soil_router

__all__ = ["weather_router", "satellite_router", "soil_router"]
