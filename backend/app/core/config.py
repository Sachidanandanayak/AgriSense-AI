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


settings = Settings()
