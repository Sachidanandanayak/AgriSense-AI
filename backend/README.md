# AgriSense AI — Backend Service

The backend of **AgriSense AI** provides the core RESTful API services that power the farm advisory platform. It is built with **FastAPI**, a modern, high-performance web framework for building APIs with Python 3.10+ based on standard Python type hints.

---

> **Current Milestone:** **Phase 7 — Multi-Source Feature Engineering**

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
| `GET` | `/api/soil` | Normalized Soil Properties & Texture | `?latitude=20.59&longitude=78.96&depth=0-5cm` |

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

---

## 🌱 Phase 6: Soil & Geospatial Data Integration

### 1. Purpose & Scope
Phase 6 establishes the digital soil data infrastructure for AgriSense AI. It provides point-based soil property lookups for farmer coordinates without requiring heavy local raster datasets, GeoTIFF downloads, or PostGIS databases.

> [!IMPORTANT]
> **Data Infrastructure Only — ML Model Untouched:**
> Soil data is ingested as an independent data source. The Random Forest ML model is **NOT** retrained, `backend/ml/` is **NOT** modified, and soil features are not substituted into the baseline model yet. Multi-source ML fusion will take place in subsequent phases.

---

### 2. Selected Soil Data Source: ISRIC SoilGrids 2.0
- **Provider**: [ISRIC — World Soil Information](https://www.isric.org/)
- **Platform**: [SoilGrids 2.0](https://soilgrids.org/)
- **Documentation**: [https://docs.isric.org/globaldata/soilgrids/](https://docs.isric.org/globaldata/soilgrids/)
- **Spatial Resolution**: Approximately **250 meters** globally.
- **Licensing & Attribution**: SoilGrids 2.0 data is publicly available under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
  *Citation*: Poggio, L., de Sousa, L. M., Batjes, N. H., et al. (2021). *SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty*. SOIL, 7, 217–240.

---

### 3. Soil Properties & Unit Conversions
SoilGrids stores and transmits integer-mapped values to optimize storage. To obtain conventional scientific and agronomic units, the raw value must be **divided by the official conversion factor (d_factor)**:

| Property | SoilGrids Layer | Mapped Units | Conversion Factor (`d_factor`) | Conventional Units | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Soil pH** | `phh2o` | $\text{pH} \times 10$ | **10** | **pH** | Soil pH measured in $1:5$ water solution (0–14 scale) |
| **Clay** | `clay` | $\text{g/kg}$ | **10** | **%** ($\text{g}/100\text{g}$) | Proportion of clay particles ($< 2\,\mu\text{m}$) |
| **Sand** | `sand` | $\text{g/kg}$ | **10** | **%** ($\text{g}/100\text{g}$) | Proportion of sand particles ($50–2000\,\mu\text{m}$) |
| **Silt** | `silt` | $\text{g/kg}$ | **10** | **%** ($\text{g}/100\text{g}$) | Proportion of silt particles ($2–50\,\mu\text{m}$) |
| **Organic Carbon** | `soc` | $\text{dg/kg}$ | **10** | **g/kg** | Soil organic carbon content in fine earth fraction |
| **Bulk Density** | `bdod` | $\text{cg/cm}^3$ | **100** | **kg/dm³** ($\text{g/cm}^3$) | Bulk density of the fine earth fraction |
| **CEC** | `cec` | $\text{mmol}(c)/\text{kg}$ | **10** | **cmol(c)/kg** | Cation Exchange Capacity at pH 7 |
| **Nitrogen** | `nitrogen` | $\text{cg/kg}$ | **100** | **g/kg** | Total nitrogen content |

> [!NOTE]
> All unit conversions are strictly implemented via explicit numeric divisions by `d_factor` in [`backend/app/services/soil_service.py`](file:///c:/Users/sachin/Pictures/Screenshots/PROJECTS/AgriSense-AI/backend/app/services/soil_service.py) according to official ISRIC documentation. No conversions are invented or estimated.

---

### 4. Standard Depth Intervals
SoilGrids models soil properties across 6 standard depth layers:
- `0-5cm` (**Default MVP depth** — represents the active agricultural seedbed and topsoil)
- `5-15cm`
- `15-30cm`
- `30-60cm`
- `60-100cm`
- `100-200cm`

---

### 5. Architecture & Provider Abstraction
To safeguard against upstream API instability, the soil integration is decoupled using a provider interface:

```text
FastAPI Route (GET /api/soil) [Param validation]
                     ↓
Soil Service (backend/app/services/soil_service.py) [Normalization & conversions]
                     ↓
Soil Provider Interface (backend/app/services/soil_provider.py) [BaseSoilProvider]
                     ↓
SoilGridsProvider (HTTP Client with timeouts & error mapping)
                     ↓
ISRIC SoilGrids 2.0 REST API (https://rest.isric.org/soilgrids/v2.0/properties/query)
```

- **Beta Service Notice & Fair Use Policy**: SoilGrids REST API v2.0 is currently a beta service without high-availability guarantees. ISRIC requests adherence to a fair-use policy (maximum 5 requests per minute). The provider abstraction isolates this dependency so alternative backends (local raster tile servers or WCS services) can be plugged in without route alterations.

---

### 6. API Endpoint & Usage

#### Endpoint
```http
GET /api/soil
```

#### Query Parameters
- `latitude` (float, required): Latitude between `-90.0` and `90.0`
- `longitude` (float, required): Longitude between `-180.0` and `180.0`
- `depth` (string, optional, default: `"0-5cm"`): Standard depth interval (`0-5cm`, `5-15cm`, `15-30cm`, `30-60cm`, `60-100cm`, `100-200cm`)

#### Example Request
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/soil?latitude=20.59&longitude=78.96&depth=0-5cm"
```

#### Normalized Response (`200 OK`)
```json
{
  "latitude": 20.59,
  "longitude": 78.96,
  "depth_interval": "0-5cm",
  "soil": {
    "ph": 7.2,
    "clay_pct": 42.1,
    "sand_pct": 19.4,
    "silt_pct": 38.5,
    "organic_carbon_g_kg": 12.1,
    "bulk_density": 1.63,
    "cec": 42.6,
    "nitrogen_g_kg": 1.34
  },
  "data_source": "ISRIC SoilGrids 2.0",
  "resolution_m": 250,
  "disclaimer": "SoilGrids predictions represent 250m resolution regional estimates and do not replace on-farm laboratory soil testing. Provided under CC BY 4.0 by ISRIC."
}
```

---

### 7. Error Handling & No Fake Data Policy

The soil service adheres to a strict **zero-fake-data policy**:
- If coordinates fall outside SoilGrids coverage (e.g., oceans, water bodies, or unmodeled land masks), it returns `404 Not Found` with a clear explanation:
  `"No soil data available from SoilGrids for the requested coordinates (location may be a water body, unmodeled area, or outside coverage)."`
- Upstream network errors and timeouts return appropriate HTTP status codes:

| Condition | Status Code | Detail Message |
| :--- | :--- | :--- |
| Latitude out of bounds (`<-90` or `>90`) | `400 Bad Request` | `"Latitude must be between -90.0 and 90.0 degrees."` |
| Longitude out of bounds (`<-180` or `>180`) | `400 Bad Request` | `"Longitude must be between -180.0 and 180.0 degrees."` |
| Unsupported depth interval | `400 Bad Request` | `"Unsupported depth interval '...'. Supported intervals: 0-5cm, ..."` |
| Water body / unmodeled mask | `404 Not Found` | `"No soil data available from SoilGrids for the requested coordinates..."` |
| Upstream rate limit exceeded | `429 Too Many Requests` | `"Soil data provider rate limit exceeded. Please try again later adhering to fair use."` |
| Malformed response from provider | `502 Bad Gateway` | `"Soil data provider returned an unexpected or malformed response."` |
| Upstream provider outage (5xx/connection failure) | `503 Service Unavailable` | `"Soil data service is temporarily unavailable due to upstream connectivity or server issues."` |
| Upstream request timeout | `504 Gateway Timeout` | `"Soil data service timed out while querying SoilGrids provider."` |

---

### 8. Limitations & Future Roadmap
- **Resolution Limit**: SoilGrids provides ~250m regional statistical predictions. It provides macroscopic soil context but does not replace laboratory physical/chemical soil test assays.
- **Point Lookup MVP**: Currently supports point coordinate queries. Future phases will support field polygon zonal averaging via GeoJSON.
- **Multi-Source ML Integration**: Soil properties are unified into multi-source feature representations in Phase 7 without retraining the baseline ML model.

---

## 🧬 Phase 7: Multi-Source Feature Engineering

### 1. Purpose & Scope
Phase 7 establishes a modular, reproducible, and leakage-free feature-engineering architecture that combines:
1. Historical agricultural measurements (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`)
2. Meteorological observations (2m air temperature, relative humidity, precipitation, wind speed)
3. Satellite earth observation indices (Sentinel-2 NDVI, NDWI, NDMI, scene counts, cloud thresholds)
4. Digital soil mapping properties (ISRIC SoilGrids pH, texture %, SOC, bulk density, CEC, Nitrogen)

into a single normalized representation (`MultiSourceObservation`) and deterministic ML feature vector (`MultiSourceFeatureVector`).

```text
RAW SOURCES (Agri, Weather, Satellite, Soil)
                    ↓
           Source Normalization
                    ↓
          Validation & Screening
       (Spatial bounds & Temporal window)
                    ↓
        Spatial & Temporal Alignment
       (Strict key verification / rejection)
                    ↓
       Feature Engineering & Derivation
       (Zero-denominator protected ratios)
                    ↓
          Unified Feature Schema
                    ↓
     Future ML Model (Phase 8 & Beyond)
```

**Scope Protection**: Phase 7 does **NOT** retrain or replace the baseline Random Forest model, does **NOT** modify existing model weights (`backend/ml/models/crop_recommendation_model.joblib`), does **NOT** alter model evaluation metrics (`metrics.json`), and does **NOT** build the final recommendation API endpoint (Phase 8).

---

### 2. Four Data Sources & Responsibilities
Each external integration layer retains strict functional separation:
- **Weather Service (`WeatherService`)**: Responsible exclusively for querying Open-Meteo and returning normalized meteorological values (`WeatherResponse`).
- **Satellite Service (`SatelliteService`)**: Responsible exclusively for querying Google Earth Engine Sentinel-2 imagery, cloud screening, zonal reduction, and index computation (`SatelliteResponse`).
- **Soil Service (`SoilService` & `SoilGridsProvider`)**: Responsible exclusively for querying ISRIC SoilGrids 2.0 REST API, depth validation, and property normalization (`SoilResponse`).
- **Feature Engineering Layer (`backend/app/services/feature_engineering/`)**: Responsible exclusively for multi-source ingestion, cross-source spatial alignment, temporal coherence verification, nutrient ratio derivation, target isolation, and deterministic feature vector assembly.

---

### 3. Spatial Alignment Rules & Assumptions
- **WGS84 Validation**: Primary target coordinates must satisfy $-90.0 \le \text{latitude} \le 90.0$ and $-180.0 \le \text{longitude} \le 180.0$.
- **Configurable Engineering Alignment Tolerance**: Default cross-source spatial tolerance is **$0.005^\circ$** ($\approx 550\,\text{m}$ at equator), configurable via `FEATURE_SPATIAL_TOLERANCE_DEG` or call-time arguments.
  - *Engineering Purpose*: Accommodates floating-point coordinate precision and provider grid-centroid snapping (~250m for SoilGrids raster cells, ~500m for Sentinel-2 buffer queries).
  - *Anti-Equivalence Caveat*: This is an **engineering alignment tolerance**, NOT an assertion of farm-boundary accuracy. Cross-source observations within tolerance do **NOT** claim to represent the exact same cadastral farm parcel.
  - Spatial mismatch beyond tolerance (e.g. Weather from Delhi and Satellite from Bangalore) is caught and rejected with `SpatialAlignmentError`.
- **Explicit Spatial Caveats**:
  - *Satellite*: Uses a point-centered circular buffer (default 500m radius), which is an environmental proxy and does **not** represent an exact farm cadastral boundary.
  - *Soil*: Uses ISRIC SoilGrids 2.0 digital soil mapping predictions at 250m grid resolution, which are regional estimates and do **not** replace laboratory soil testing.
  - *Weather*: Uses Open-Meteo atmospheric model grid interpolation for the requested coordinates.

---

### 4. Temporal Alignment Rules & Handling of Static vs Dynamic Data
- **Dynamic Meteorological Observations**: Weather has an instantaneous or forecast timestamp (`weather_timestamp`).
- **Aggregated Satellite Composites**: Sentinel-2 data is aggregated over an explicit compositing window (`start_date` to `end_date`, requiring $\text{start\_date} \le \text{end\_date}$).
- **Static Pedological Context**: ISRIC SoilGrids data represents static digital soil mapping predictions for specific depth intervals (`0-5cm` default). **Soil data is never assigned an invented observation date.**
- **Configurable Engineering Temporal Margins**:
  - *Satellite Window Margin*: Default **14 days** (`FEATURE_SATELLITE_MAX_WINDOW_DAYS`), accommodating Sentinel-2's ~5-day orbital revisit to obtain 2-3 cloud-screened scenes.
  - *Weather Observation Gap*: Default **7 days** (`FEATURE_WEATHER_MAX_GAP_DAYS`), defining allowable temporal proximity around an observation date.
  - *Caveat*: These are **engineering alignment tolerances** for remote-sensing revisits and meteorological indexing, NOT universal agronomic constants across disparate crop phenological cycles.
- **Anti-Leakage Enforcement**:
  - Observations occurring strictly in the future relative to `observation_date` (e.g. satellite window starting after planting date, or future weather timestamps) are strictly rejected with `TemporalAlignmentError` to prevent forward information leakage into prediction-time feature sets.


---

### 5. Feature Normalization & Disambiguation
To eliminate duplicate ambiguous field names across sources, all features are explicitly prefixed and disambiguated:
- `historical_temperature` (seasonal mean from crop dataset) vs `weather_temperature` (air temperature from meteorological service).
- `historical_humidity` (mean relative humidity from crop dataset) vs `weather_humidity` (meteorological relative humidity %).
- `historical_rainfall` (seasonal cumulative precipitation) vs `weather_precipitation` (meteorological rainfall depth).
- `historical_ph` (measured soil pH from crop dataset) vs `soil_ph` (SoilGrids digital soil map pH).
- `nitrogen` (available N from fertilizer/soil test) vs `soil_nitrogen_g_kg` (total fine-earth N from SoilGrids).

No source silently overwrites another.

---

### 6. Scientifically Defensible Derived Agronomic Features
Nutrient stoichiometry and balance ratios are computed using `safe_ratio()`:
- **$N/P$ Ratio**: $\text{Nitrogen} / \text{Phosphorus}$
- **$N/K$ Ratio**: $\text{Nitrogen} / \text{Potassium}$
- **$P/K$ Ratio**: $\text{Phosphorus} / \text{Potassium}$

**Anti-Fabrication & Zero-Denominator Policy**:
- When a denominator is zero, negative, or missing, the derived ratio evaluates strictly to `None` (null).
- No arbitrary epsilon, synthetic zero, mean, or median is injected into the feature representation during Phase 7.
- Satellite indices (NDVI, NDWI, NDMI) preserve their original mathematical formulas and $[-1.0, 1.0]$ bounds. They are **never** reinterpreted as arbitrary crop suitability percentages.

---

### 7. Missing-Data Policy
- Missing values across all sources (e.g., failed weather API call, cloud-obscured satellite composite, unmodeled SoilGrids point) are **explicitly preserved as `None` (null)**.
- Imputation (mean, median, KNN, iterative) is intentionally deferred to the future ML model training pipeline where an explicit, cross-validated imputation strategy can be formally defined.

---

### 8. Data Leakage Prevention
- **Supervised Target Isolation**: The ground-truth crop classification label (`crop_label` / `label`) is strictly separated from feature vectors.
- `to_feature_dict(include_target=False)` and `to_feature_vector()` completely omit `crop_label`.
- `validate_no_target_leakage()` proactively scans feature dictionaries and raises `DataLeakageError` if target keys (`crop_label`, `label`, `target`, `crop`) are present in prediction inputs.
- Metadata (coordinates, timestamps, data providers) are strictly excluded from prediction vectors.

---

### 9. Historical Dataset Limitations & Anti-Fabrication Rule
> **"The current benchmark agricultural dataset lacks the geospatial and temporal keys required to legitimately join live weather, satellite, and soil observations. Therefore, Phase 7 creates the multi-source feature contract and alignment infrastructure without fabricating historical environmental observations."**

The raw benchmark dataset (`backend/data/raw/Crop_recommendation.csv`) contains 2,200 records across 22 crops, but lacks farmer GPS coordinates, planting dates, and farm boundaries.
- **Strict Anti-Fabrication**: We do **not** assign arbitrary coordinates, today's weather, or SoilGrids predictions to historical rows.
- **Dataset Immutability**: `backend/data/raw/Crop_recommendation.csv` remains strictly unchanged.

---

### 10. Machine-Readable Feature Schema
The complete schema contract is defined in `backend/ml/datasets/multisource_feature_schema.json`, documenting all 27 input features, data types, units, physical meanings, spatial/temporal meanings, and anti-leakage policies:

| Index | Feature Name | Source | Datatype | Unit | Nature |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `nitrogen` | Agricultural | float | kg/ha | Raw |
| 2 | `phosphorus` | Agricultural | float | kg/ha | Raw |
| 3 | `potassium` | Agricultural | float | kg/ha | Raw |
| 4 | `historical_temperature` | Agricultural | float | °C | Raw |
| 5 | `historical_humidity` | Agricultural | float | % | Raw |
| 6 | `historical_ph` | Agricultural | float | pH scale (0-14) | Raw |
| 7 | `historical_rainfall` | Agricultural | float | mm | Raw |
| 8 | `n_p_ratio` | Derived | float | ratio | Derived |
| 9 | `n_k_ratio` | Derived | float | ratio | Derived |
| 10 | `p_k_ratio` | Derived | float | ratio | Derived |
| 11 | `weather_temperature` | Weather | float | °C | Raw |
| 12 | `weather_humidity` | Weather | float | % | Raw |
| 13 | `weather_precipitation` | Weather | float | mm | Raw |
| 14 | `weather_wind_speed` | Weather | float | m/s | Raw |
| 15 | `satellite_ndvi` | Satellite | float | index (-1 to 1) | Derived |
| 16 | `satellite_ndwi` | Satellite | float | index (-1 to 1) | Derived |
| 17 | `satellite_ndmi` | Satellite | float | index (-1 to 1) | Derived |
| 18 | `satellite_usable_observations` | Satellite | int | count | Raw |
| 19 | `satellite_cloud_probability_threshold` | Satellite | float | % | Raw |
| 20 | `soil_ph` | Soil | float | pH scale (0-14) | Raw |
| 21 | `soil_clay_pct` | Soil | float | % | Raw |
| 22 | `soil_sand_pct` | Soil | float | % | Raw |
| 23 | `soil_silt_pct` | Soil | float | % | Raw |
| 24 | `soil_organic_carbon_g_kg` | Soil | float | g/kg | Raw |
| 25 | `soil_bulk_density` | Soil | float | kg/dm³ | Raw |
| 26 | `soil_cec` | Soil | float | cmol(c)/kg | Raw |
| 27 | `soil_nitrogen_g_kg` | Soil | float | g/kg | Raw |

---

### 11. Deterministic Feature Vector Generation
The builder produces an ordered list of 27 values via `to_feature_vector()` that guarantees deterministic consistency across repeated calls, with zero metadata and zero target contamination:

```python
from app.services.feature_engineering import feature_builder

obs = feature_builder.build_unified_observation(
    latitude=16.20,
    longitude=77.35,
    observation_date="2026-09-25",
    weather=weather_response,
    satellite=satellite_response,
    soil=soil_response,
    agricultural_data={"N": 80.0, "P": 40.0, "K": 40.0},
)

# Extract deterministic ML feature vector (27 elements)
feature_vector = obs.to_feature_vector()
```

---

### 12. Automated Testing & Verification
The test suite in `backend/tests/test_feature_engineering.py` covers all Phase 7 validation requirements and runs as part of the unified test suite (136 tests total):
```powershell
python -m unittest discover -s backend/tests -p "test_*.py"
# Ran 136 tests in ~2s - OK (skipped=2)
```



