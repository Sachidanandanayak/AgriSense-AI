"""Application configuration and settings for AgriSense AI."""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in backend/ or repository root
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = "AgriSense AI API"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # Weather Provider Configuration (Open-Meteo)
    WEATHER_API_KEY: str | None = os.getenv("WEATHER_API_KEY") or None
    WEATHER_BASE_URL: str = os.getenv(
        "WEATHER_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )
    WEATHER_TIMEOUT_SECONDS: float = float(
        os.getenv("WEATHER_TIMEOUT_SECONDS", "10.0")
    )

    # Satellite Provider Configuration (Google Earth Engine)
    EARTHENGINE_PROJECT: str | None = (
        os.getenv("EARTHENGINE_PROJECT") or os.getenv("EE_PROJECT_ID") or None
    )
    EARTHENGINE_SERVICE_ACCOUNT: str | None = (
        os.getenv("EARTHENGINE_SERVICE_ACCOUNT") or None
    )
    EARTHENGINE_KEY_FILE: str | None = os.getenv("EARTHENGINE_KEY_FILE") or None
    EARTHENGINE_PRIVATE_KEY: str | None = os.getenv("EARTHENGINE_PRIVATE_KEY") or None
    EARTHENGINE_TIMEOUT_SECONDS: float = float(
        os.getenv("EARTHENGINE_TIMEOUT_SECONDS", "25.0")
    )

    # Satellite Analysis Defaults
    SATELLITE_DEFAULT_RADIUS_M: float = float(
        os.getenv("SATELLITE_DEFAULT_RADIUS_M", "500.0")
    )
    SATELLITE_DEFAULT_CLOUD_THRESHOLD: float = float(
        os.getenv("SATELLITE_DEFAULT_CLOUD_THRESHOLD", "65.0")
    )


settings = Settings()
