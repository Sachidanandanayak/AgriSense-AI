from fastapi import FastAPI
from app.api.routes.weather import router as weather_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Satellite & AI-Powered Crop Suitability and Farm Advisory Platform API",
    version=settings.VERSION,
)

# Register API routers
app.include_router(weather_router, prefix=settings.API_PREFIX, tags=["Weather"])


@app.get("/")
def read_root():
    return {"message": "Welcome to AgriSense AI API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
