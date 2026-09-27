# AgriSense AI — Backend Service

The backend of **AgriSense AI** provides the core RESTful API services that power the farm advisory platform. It is built with **FastAPI**, a modern, high-performance web framework for building APIs with Python 3.10+ based on standard Python type hints.

---

> **Current Milestone:** **Phase 5 — Satellite Data Integration**

---

## ⚡ API Endpoints

| Method | Endpoint | Description | Sample Query / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root / Welcome Message | `{"message": "Welcome to AgriSense AI API"}` |
| `GET` | `/health` | Service Health & Readiness Probe | `{"status": "healthy"}` |
| `GET` | `/docs` | Interactive Swagger UI API Docs | Interactive UI (`text/html`) |
| `GET` | `/redoc` | Interactive ReDoc API Docs | Interactive UI (`text/html`) |
| `GET` | `/api/weather` | Current Normalized Weather Observations | `?latitude=16.20&longitude=77.35` |
| `GET` | `/api/satellite` | Sentinel-2 Vegetation & Moisture Indices | `?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25` |

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

### 5. Query Satellite Endpoint
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25&radius_m=500"
```

---

## 🛰️ Phase 5: Satellite Data Integration

### 1. Selected Satellite Provider & Platform: Google Earth Engine
- **Platform**: [Google Earth Engine (GEE)](https://earthengine.google.com/)
- **Python Client**: `earthengine-api>=1.7.0`
- **Why Google Earth Engine was selected**:
  1. **Server-Side Geospatial Processing**: Performs pixel-level cloud masking, spatial filtering, temporal reduction, and regional zonal statistics directly on Google Cloud infrastructure.
  2. **Zero Local Storage Overhead**: Eliminates the need to download and store multi-gigabyte Sentinel-2 raster granules (JPEG2000 / SAFE archives) on developer machines or inside Git repositories.
  3. **On-Demand Precision Querying**: Retrieves only the targeted statistical observations required for a farmer's coordinates and requested temporal window.
  4. **Production Scalability**: Seamlessly handles spatial buffering, harmonized collections, and dynamic scaling across arbitrary coordinates worldwide.

---

### 2. Selected Satellite Dataset & Spectral Bands
- **Harmonized Surface Reflectance Collection**: `COPERNICUS/S2_SR_HARMONIZED`
  - Multi-spectral, orthorectified bottom-of-atmosphere (BOA) reflectance.
  - Harmonized processing aligns baseline offsets between Sentinel-2A and Sentinel-2B.
- **Cloud Probability Collection**: `COPERNICUS/S2_CLOUD_PROBABILITY`
  - Sentinel-2 cloud probability dataset generated by the European Space Agency / Sentinel Hub via gradient boosting algorithms.
  - Provides pixel-level cloud probability values ranging from 0% to 100%.
- **Why Sentinel-2 was selected**:
  - High spatial resolution (10m for RGB/NIR, 20m for SWIR/Red Edge).
  - High temporal revisit cadence (approx. 5 days with Sentinel-2A and Sentinel-2B constellation).
  - Optimal spectral coverage tailored for agronomic and vegetation health monitoring.
- **Spectral Bands Used**:
  - **B3 (Green)**: 560 nm (10m resolution)
  - **B4 (Red)**: 665 nm (10m resolution)
  - **B8 (Near-Infrared / NIR)**: 842 nm (10m resolution)
  - **B11 (Short-Wave Infrared / SWIR)**: 1610 nm (20m resolution)

---

### 3. Spectral Index Formulas & Interpretations

#### A. NDVI — Normalized Difference Vegetation Index
$$\text{NDVI} = \frac{B8 - B4}{B8 + B4} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$
- **Purpose**: Evaluates live green vegetation canopy density, vigor, and chlorophyll absorption.
- **Dynamic Range**: `[-1.0, 1.0]`. Dense healthy crops typically exhibit values between `0.4` and `0.85`; bare soil yields `0.05` to `0.20`; water bodies and clouds yield values `< 0.0`.
- **Zero Denominator Protection**: Safely returns `0.0` when $|B8 + B4| < 10^{-7}$.

#### B. NDWI — Normalized Difference Water Index (McFeeters 1996)
$$\text{NDWI} = \frac{B3 - B8}{B3 + B8} = \frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$$
- **Important Definition Note**: In remote sensing literature, two distinct indices are called "NDWI":
  1. **McFeeters (1996)**: $\frac{\text{Green} - \text{NIR}}{\text{Green} + \text{NIR}}$ (delineates surface water bodies and water-logging).
  2. **Gao (1996)**: $\frac{\text{NIR} - \text{SWIR}}{\text{NIR} + \text{SWIR}}$ (measures canopy moisture content).
- **AgriSense AI Standard**: We strictly adopt the **McFeeters (1996)** formulation for **NDWI** to monitor open surface water, localized ponding, drainage bottlenecks, and flood inundation. Open water bodies show positive values ($> 0.0$), whereas terrestrial vegetation and soil yield negative values.
- **Zero Denominator Protection**: Safely returns `0.0` when $|B3 + B8| < 10^{-7}$.

#### C. NDMI — Normalized Difference Moisture Index (Gao 1996)
$$\text{NDMI} = \frac{B8 - B11}{B8 + B11} = \frac{\text{NIR} - \text{SWIR}}{\text{NIR} + \text{SWIR}}$$
- **Purpose**: Measures liquid water content stored within crop leaf canopies and spongy mesophyll cellular structure.
- **Dynamic Range**: `[-1.0, 1.0]`. Well-hydrated crop canopies exhibit positive values (`0.2` to `0.5`); water-stressed crops or drought-affected fields drop toward `0.0` or negative values.
- **Zero Denominator Protection**: Safely returns `0.0` when $|B8 + B11| < 10^{-7}$.

---

### 4. Cloud Filtering Strategy
Instead of coarse scene-level cloud metadata (which often discards clear fields inside partially cloudy granules), AgriSense AI performs **pixel-level masking**:
1. Joins the Sentinel-2 Surface Reflectance collection with the matching `COPERNICUS/S2_CLOUD_PROBABILITY` collection by granule index (`system:index`).
2. Applies a configurable cloud probability threshold (default: **65%**):
   $$\text{Mask} = \text{Cloud Probability} < 65\%$$
3. Pixels exceeding the threshold are masked out of the computation.
4. If no cloud-free pixels remain across the entire temporal window, the API returns a clean HTTP 404 response:
   `"No suitable cloud-free Sentinel-2 observation was found for the requested location and date range."`

---

### 5. Temporal Composite & Spatial Aggregation

#### Temporal Composite
- Observations over the requested window (`start_date` to `end_date`) are composited using a **median reducer**:
  $$\text{Composite} = \text{median}(\text{Cloud-Masked Collection})$$
- **Rationale**: The temporal median composite removes transient atmospheric artifacts, shadows, residual sub-pixel clouds, and sensor noise while retaining authentic ground reflectance.
- The service tracks and returns the count of usable observations (`usable_observations`).

#### Spatial Aggregation
- **Point-Centered Circular Buffer**: The user provides a center coordinate (`latitude`, `longitude`) and an optional radius (`radius_m`, default: 500 meters).
- **Zonal Reducer**: Spectral indices are aggregated over the circular region:
  - **Median**: Primary robust central tendency indicator (`ndvi_median`, `ndwi_median`, `ndmi_median`).
  - **Comprehensive Statistics**: Regional min, max, mean, median, and standard deviation are computed and provided in the `statistics` object.

---

### 6. Normalized Satellite Response Schema

**Example Request**:
```http
GET /api/satellite?latitude=16.20&longitude=77.35&start_date=2026-09-01&end_date=2026-09-25&radius_m=500&cloud_probability_threshold=65
```

**Normalized Response (`200 OK`)**:
```json
{
  "latitude": 16.20,
  "longitude": 77.35,
  "radius_m": 500.0,
  "start_date": "2026-09-01",
  "end_date": "2026-09-25",
  "usable_observations": 3,
  "cloud_probability_threshold": 65.0,
  "ndvi_median": 0.54,
  "ndwi_median": 0.18,
  "ndmi_median": 0.31,
  "data_source": "Sentinel-2",
  "statistics": {
    "ndvi": { "min": 0.31, "max": 0.72, "mean": 0.528, "median": 0.54, "std_dev": 0.085 },
    "ndwi": { "min": -0.21, "max": 0.45, "mean": 0.175, "median": 0.18, "std_dev": 0.091 },
    "ndmi": { "min": 0.12, "max": 0.48, "mean": 0.301, "median": 0.31, "std_dev": 0.062 }
  },
  "disclaimer": "The current implementation uses a point-centered analysis radius and therefore does not represent an exact farm boundary. Satellite indices are environmental indicators and are not direct crop-suitability scores."
}
```

---

### 7. Google Earth Engine Setup & Authentication

#### Prerequisites
1. **Google Earth Engine Account**: Register a free research or commercial account at [earthengine.google.com](https://earthengine.google.com/).
2. **Google Cloud Project**: An active GCP project with the Earth Engine API (`earthengine.googleapis.com`) enabled.

#### Authentication Process

##### A. Local Development (Interactive OAuth)
1. Run the official Earth Engine authentication command:
   ```powershell
   earthengine authenticate
   ```
2. Follow the browser authorization prompt to log in with your Google account. Credentials are stored securely in `~/.config/earthengine/credentials`.
3. Set your Google Cloud Project ID in your `.env` file:
   ```bash
   EARTHENGINE_PROJECT=your-gcp-project-id
   ```

##### B. Automated / Server Deployment (Service Account)
1. In Google Cloud Console, create a Service Account with Earth Engine Resource Viewer / Earth Engine User roles.
2. Generate and download a JSON key file.
3. Configure the environment variables:
   ```bash
   EARTHENGINE_PROJECT=your-gcp-project-id
   EARTHENGINE_SERVICE_ACCOUNT=service-account@project.iam.gserviceaccount.com
   EARTHENGINE_KEY_FILE=/path/to/service-account-key.json
   ```

> [!CAUTION]
> **Credential Security**: Never commit service account JSON keys, `.env` files, or private keys to Git. `.gitignore` is strictly configured to ignore `*.json` key files and credentials.

---

### 8. Critical Agronomic & Architecture Disclaimers

> [!IMPORTANT]
> **"The current implementation uses a point-centered analysis radius and therefore does not represent an exact farm boundary."**
>
> In the Phase 5 MVP, a circular buffer (default: 500m) is analyzed around the farmer's coordinate. This buffer may capture neighboring plots, road verges, or non-cropped vegetation. Future phases will support user-uploaded farm polygons (GeoJSON, KML, Shapefile) for precise field-boundary zonal extraction.

> [!IMPORTANT]
> **"Satellite indices are environmental indicators and are not direct crop-suitability scores."**
>
> - NDVI indicates photosynthetic activity and biomass density.
> - NDWI indicates surface water and ponding.
> - NDMI indicates canopy hydration and moisture stress.
>
> In Phase 5, satellite data is purely **DATA INFRASTRUCTURE**. It is not fed into the baseline Random Forest model, and the ML model has **NOT** been retrained. Satellite indices will be integrated into the multi-source crop suitability engine only after comprehensive feature engineering combining weather, soil, and historical data.

---

### 9. Current Limitations & Future Roadmap
- **Point-Based Analysis**: Circular buffer approximation rather than exact field cadastral boundaries.
- **Revisit Latency**: Sentinel-2 observations occur every ~5 days; cloud cover may require extending the query window.
- **Future Enhancements**:
  - GeoJSON farm polygon boundary upload.
  - Multi-field spatial aggregation.
  - Phenological time-series trajectory tracking (NDVI curve slope for sowing/harvest detection).
