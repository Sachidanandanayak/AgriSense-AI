from fastapi import FastAPI

app = FastAPI(
    title="AgriSense AI API",
    description="Satellite & AI-Powered Crop Suitability and Farm Advisory Platform API",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to AgriSense AI API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
