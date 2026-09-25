# AgriSense AI — Backend Service

The backend of **AgriSense AI** provides the core RESTful API services that power the farm advisory platform. It is built with **FastAPI**, a modern, high-performance web framework for building APIs with Python 3.10+ based on standard Python type hints.

---

> **Current Milestone:** **Phase 4 — Weather Data Integration**

---

## ⚡ API Endpoints

| Method | Endpoint | Description | Sample Query / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root / Welcome Message | `{"message": "Welcome to AgriSense AI API"}` |
| `GET` | `/health` | Service Health & Readiness Probe | `{"status": "healthy"}` |
| `GET` | `/docs` | Interactive Swagger UI API Docs | Interactive UI (`text/html`) |
| `GET` | `/redoc` | Interactive ReDoc API Docs | Interactive UI (`text/html`) |
| `GET` | `/api/weather` | Current Normalized Weather Observations | `?latitude=16.20&longitude=77.35` (See Schema below) |

---

## 🌦️ Phase 4: Weather Data Integration

### 1. Selected Weather Provider: Open-Meteo
- **Provider Name**: [Open-Meteo Weather Forecast API](https://open-meteo.com/en/docs)
- **API Documentation**: [https://open-meteo.com/en/docs](https://open-meteo.com/en/docs)
- **Rationale for Selection**:
  1. **No API Key Required for Development**: Open-Meteo provides immediate development and CI onboarding without mandatory API keys or billing friction.
  2. **Precise Coordinate Support**: Directly takes `latitude` and `longitude` query parameters without requiring reverse-geocoding into city names.
  3. **High Resolution & Real-Time Meteorological Data**: Ingests open data from premier meteorological organizations (ECMWF, NOAA GFS, DWD ICON, JMA).
  4. **Native Metric Units**: Supports returning temperature in Celsius, precipitation in millimeters, and wind speed in meters per second (`&wind_speed_unit=ms`).
  5. **Forecast & Observation Breadth**: Supports current observations, hourly variables, multi-day forecasts, and agricultural soil moisture parameters for future phases.
- **Free-Tier Limitations**:
  - Up to 10,000 API calls per day for non-commercial/development use.
  - Rate limiting of approximately 600 requests/minute.
  - High-volume commercial deployments can configure a paid API key via `WEATHER_API_KEY`.

---

### 2. Architecture & Data Flow

```text
Farmer / Client Coordinates (latitude, longitude)
                       ↓
FastAPI Route (/api/weather) [Param Validation]
                       ↓
Weather Service (backend/app/services/weather_service.py)
                       ↓
Upstream Weather API (Open-Meteo REST Service)
                       ↓
Data Normalization & Resilience Layer
                       ↓
Pydantic Response Schema (backend/app/schemas/weather.py)
                       ↓
Validated JSON Response
```

The external weather provider's raw payload is **never exposed directly** to the client. The service normalizes provider data into AgriSense AI's unified schema.

---

### 3. Normalized Weather Response Schema

**Example Request**:
```http
GET /api/weather?latitude=16.20&longitude=77.35
```

**Normalized Response (`200 OK`)**:
```json
{
  "latitude": 16.2,
  "longitude": 77.35,
  "temperature_c": 27.2,
  "humidity_percent": 59.0,
  "rainfall_mm": 0.0,
  "wind_speed_mps": 3.91,
  "weather_timestamp": "2026-09-25T17:15"
}
```

#### Field Specifications & Units

| Field Name | Type | Physical Bounds | Unit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `latitude` | `float` | `[-90.0, 90.0]` | Decimal degrees | Requested latitude coordinate |
| `longitude` | `float` | `[-180.0, 180.0]` | Decimal degrees | Requested longitude coordinate |
| `temperature_c` | `float` | `[-100.0, 70.0]` | `°C` (Celsius) | 2-meter air temperature |
| `humidity_percent` | `float` | `[0.0, 100.0]` | `%` | 2-meter relative humidity |
| `rainfall_mm` | `float` | `≥ 0.0` | `mm` | Current precipitation / rainfall depth |
| `wind_speed_mps` | `float` | `≥ 0.0` | `m/s` | 10-meter wind speed |
| `weather_timestamp` | `str` | ISO 8601 | Datetime | Observation timestamp |

---

### 4. Error Handling & Resilience

The service implements graceful degradation with clear HTTP status codes without exposing internal tracebacks:

| Condition | Status Code | Error Message / Detail |
| :--- | :--- | :--- |
| Latitude out of bounds (`<-90` or `>90`) | `400 Bad Request` | `"Latitude must be between -90.0 and 90.0 degrees."` |
| Longitude out of bounds (`<-180` or `>180`) | `400 Bad Request` | `"Longitude must be between -180.0 and 180.0 degrees."` |
| Missing required query parameters | `422 Unprocessable` | FastAPI validation error detail |
| Provider rate limit exceeded | `429 Too Many Requests` | `"Weather provider rate limit exceeded. Please try again later."` |
| Provider returns 5xx error or invalid payload | `502 Bad Gateway` | `"Weather provider returned an invalid or error response."` |
| Upstream network connection failure | `503 Service Unavailable` | `"Weather service is temporarily unavailable due to network issues."` |
| Upstream request timeout | `504 Gateway Timeout` | `"Weather service timed out while contacting upstream provider."` |

---

### 5. Configuration & Environment Variables

Environment variables are managed cleanly via `backend/app/core/config.py` using `.env` files.

Template (`.env.example`):
```bash
# Weather Provider Configuration
WEATHER_API_KEY=your_weather_api_key_here
WEATHER_BASE_URL=https://api.open-meteo.com/v1/forecast
WEATHER_TIMEOUT_SECONDS=10.0
```

> **Security Note**: Never commit `.env` containing sensitive credentials to git. `.gitignore` is configured to exclude `.env` while preserving `.env.example`.

---

### 6. Testing Strategy

The test suite is located in `backend/tests/test_weather.py` and adheres strictly to network isolation:
- **Zero Internet Dependency**: All unit and endpoint tests mock upstream HTTP requests with `AsyncMock` and `httpx.Response`.
- **Coverage**:
  - Successful weather response retrieval and field normalization.
  - Latitude and longitude boundary validations.
  - API timeouts, rate limits (429), and upstream 500 errors.
  - Network connection failures and offline fallback.
  - Missing provider blocks or missing observation fields.
  - Pydantic schema validation for ranges and non-negative constraints.
  - Regression verification for existing `GET /`, `GET /health`, and `GET /docs`.

Execute tests:
```powershell
python -m unittest tests/test_weather.py
```
Or run the full suite:
```powershell
python -m unittest discover tests
```

---

### 7. Important ML Integration & Agronomic Distinction

> [!IMPORTANT]
> **Weather Data is Currently Data Infrastructure — Not an ML Feature Substitution.**
>
> In Phase 4:
> - The Random Forest baseline crop recommendation model (Phase 3) is **NOT** modified or retrained.
> - Current live weather readings are **NOT** claimed to improve model accuracy.
> - **Agronomic Distinction**: The Kaggle benchmark dataset used in Phase 2/3 contains seasonal average environmental features (`temperature`, `humidity`, `rainfall`). Live single-point weather observations are **not equivalent** to seasonal climate features:
>   - *Current Temperature ≠ Seasonal Growing Temperature*
>   - *Current Hourly Rainfall ≠ Seasonal Accumulated Rainfall*
>   - *Current Relative Humidity ≠ Long-Term Humidity Pattern*
>
> Future phases will engineer multi-source agro-climatic features (such as 7-day, 30-day, and seasonal accumulated rainfall, thermal unit sums, and weather anomalies) prior to feeding live weather into ML models.

---

### 8. Current Limitations
- **Point-in-Time Observations**: Only current weather observations are exposed via `/api/weather`. Multi-day forecasts and historical aggregates are scheduled for subsequent advisory phases.
- **Provider Redundancy**: A single primary provider (Open-Meteo) is integrated. Secondary fallback providers (e.g., NASA POWER) will be evaluated in future iterations.

---

## 💻 Getting Started (Windows PowerShell)

### 1. Activate Virtual Environment
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

### 3. Run FastAPI Server
```powershell
uvicorn app.main:app --reload
```
Server runs at `http://127.0.0.1:8000`.

### 4. Query Weather Endpoint
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/weather?latitude=16.20&longitude=77.35"
```
