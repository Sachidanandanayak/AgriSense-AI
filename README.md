# AgriSense AI 🌾🛰️

**Satellite & AI-Powered Crop Suitability and Farm Advisory Platform**

---

> **Current Development Status:** **Phase 8 — Crop Suitability & Recommendation Engine**

---

## 📌 Overview

**AgriSense AI** is an intelligent agricultural advisory platform designed to bridge the gap between complex remote-sensing data, weather patterns, soil health metrics, and on-the-ground farming decisions. By leveraging satellite observations, meteorological forecasts, historical agricultural records, and machine learning, AgriSense AI provides farmers and agricultural stakeholders with actionable, localized crop suitability assessments and risk-aware advisory services.

---

## ⚠️ The Problem

Modern agriculture faces unprecedented challenges due to climate variability, unpredictable weather events, depleting ground water resources, and soil degradation:
- **Suboptimal Crop Selection**: Farmers frequently rely on traditional, anecdotal knowledge or market trends rather than localized ecological and soil suitability, leading to reduced yields and financial vulnerability.
- **Resource Inefficiency**: Inappropriate crop choices result in excessive irrigation demands and inefficient fertilizer application.
- **Climate & Weather Risk**: Unforeseen weather extremes (droughts, unseasonal rainfall, temperature spikes) cause crop failures that could be mitigated with predictive insights.
- **Data Fragmentation**: While satellite imagery, weather feeds, and soil surveys exist, they are isolated, technical, and largely inaccessible to everyday farmers and farm managers.

---

## 💡 The Proposed Solution

AgriSense AI synthesizes multi-source environmental and geospatial data into straightforward, high-confidence farming intelligence. By ingesting basic farmer inputs (location coordinates, acreage, season, irrigation infrastructure, and optional soil test reports) and pairing them with earth observation and machine learning models, the platform delivers:

1. **Crop Suitability Scores**: Ranked recommendations for crops with the highest probability of success in the target microclimate and soil profile.
2. **Resource Metrics**: Estimated water consumption, irrigation requirements, and approximate growing durations.
3. **Environmental & Weather Risk Assessments**: Clear warnings regarding drought risk, heat stress, or moisture excess.
4. **Transparent Explanations**: Transparent rationale explaining *why* a particular crop is recommended or cautioned against.

---

## 🏗️ Major Planned Components

The platform architecture is designed across several core functional modules:

- **1. Farmer Input Module**  
  Captures farmer-specific farm context including geographic location (GPS / boundary / district), farm area, planned growing season, irrigation type/availability, and optional N-P-K / pH soil test parameters.

- **2. Weather Data Service**  
  Integrates historical, current, and forecasted meteorological data (rainfall patterns, temperature profiles, solar radiation, humidity, and evapotranspiration rates).

- **3. Satellite Observation Engine**  
  Retrieves and processes remote-sensing indices (such as NDVI for vegetation vigour, NDWI for water/moisture stress, and surface reflectance) to understand historical field performance and land conditions.

- **4. Soil Data Service**  
  Blends local farmer-provided soil data with regional digital soil maps and global soil databases (texture, organic carbon content, drainage, pH).

- **5. Historical Agricultural Data Layer**  
  Correlates regional agro-climatic zones, historical crop yield statistics, and seasonal crop calendars.

- **6. Multi-Source Feature Engineering Engine (Phase 7)**  
  Normalizes, aligns (spatially & temporally), validates, and constructs deterministic feature vectors across agricultural, meteorological, satellite, and soil sources without data leakage or fabrication.

- **7. Machine Learning Engine**  
  Trained on multi-dimensional agro-climatic datasets to predict crop suitability classifications, yield potential tiers, and viability scores.

- **8. Crop Recommendation & Advisory System (Phase 8)**  
  Orchestrates the benchmark ML model with live/cached weather, Sentinel-2 satellite, and SoilGrids data to provide top-K ranked recommendations, model probability estimates, provenance, and data-grounded explanations.

- **9. Environmental Risk Analysis**  
  Evaluates environmental vulnerability—such as late-season heat stress, flood vulnerability, or prolonged dry spells—and provides mitigation advisories.

- **10. Farmer Dashboard (Frontend)**  
  A clean, intuitive, and responsive web interface designed to present complex geospatial insights through clear visual cards, charts, maps, and straightforward advisory summaries.

---

## 🛠️ Planned Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & API** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **Data Processing & ML** | NumPy, Pandas, Scikit-learn, XGBoost / LightGBM, Joblib |
| **Geospatial & Satellite** | Earth Engine API / Sentinel Hub / Planetary Computer, Rasterio, GeoPandas |
| **Weather APIs** | Open-Meteo / NASA POWER / NOAA APIs |
| **Soil Providers** | ISRIC SoilGrids 2.0 REST API |
| **Feature Engineering** | Pydantic V2 Schemas, Domain-Specific Stoichiometric Ratios, Spatial/Temporal Validators |
| **Frontend** | Modern Web Framework (React / Next.js / Vite), Responsive CSS |
| **Storage & Caching** | PostgreSQL / PostGIS (Planned), Redis (Planned) |
| **Testing & CI** | Unittest, Pytest |

---

## 📁 Repository Structure

```text
AgriSense-AI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/                 # API router configurations
│   │   │   ├── __init__.py
│   │   │   └── routes/          # Endpoints: weather, satellite, soil, recommendations
│   │   ├── core/                # App configuration, settings, logging
│   │   ├── models/              # Internal domain models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic services
│   │   │   ├── weather_service.py
│   │   │   ├── satellite_service.py
│   │   │   ├── soil_service.py
│   │   │   ├── soil_provider.py
│   │   │   ├── feature_engineering/ # Multi-source feature orchestration (Phase 7)
│   │   │   │   ├── schemas.py      # Unified multi-source contracts
│   │   │   │   ├── normalizer.py   # Source normalization
│   │   │   │   ├── builder.py      # Feature engineering builder
│   │   │   │   └── validators.py   # Spatial/temporal/leakage validation
│   │   │   └── recommendation/      # Production recommendation engine (Phase 8)
│   │   │       ├── schemas.py      # Request/response contracts & advisory items
│   │   │       ├── model_adapter.py# Safe 11-feature model adapter & probability estimator
│   │   │       ├── recommendation_service.py # Orchestrator & environmental context
│   │   │       ├── explanation.py  # Transparent explanations & limitations
│   │   │       └── validators.py   # Boundary & non-null input validators
│   │   └── utils/               # Shared helpers and formatters
│   ├── tests/                   # Backend automated test suite (171 tests passed)
│   ├── data/
│   │   ├── raw/                 # Raw agricultural benchmark data (Crop_recommendation.csv)
│   │   └── processed/           # Feature-engineered splits & boundary docs
│   ├── ml/
│   │   ├── datasets/            # multisource_feature_schema.json
│   │   ├── notebooks/           # Exploratory data analysis & model experiments
│   │   ├── models/              # Baseline Random Forest model (unchanged)
│   │   └── scripts/             # Validation and preparation pipelines
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Detailed backend documentation
├── frontend/                    # Web dashboard (to be built in upcoming phases)
├── .gitignore                   # Version control ignore rules
└── README.md                    # Project documentation
```

---

## 🚀 Current Milestone: Phase 8 — Crop Suitability & Recommendation Engine

> **Mandatory Scientific Notice:**  
> *"The current recommendation engine is a benchmark-model recommendation layer augmented with environmental context. It is not yet a field-validated crop suitability or yield prediction system."*

### Key Accomplishments in Phase 8
1. **Model Compatibility Boundary**:
   - Explicitly identified the 11 feature columns consumed by the trained Random Forest model (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `N_P_ratio`, `N_K_ratio`, `P_K_ratio`, `rain_temp_ratio`).
   - Built `CropModelAdapter` to isolate the 11 model features from the 27 Phase 7 multi-source feature vector without silent dropping or reordering.
2. **Probability Estimate Terminology**:
   - Output uses `probability_estimate` and `confidence_percentage`. Prohibits misleading claims like "suitability percentage", "harvest success probability", or "yield probability".
3. **Data-Grounded Explanations & Limitations**:
   - Transparent explanations cite exact observed values (temperature, rainfall, NDVI, soil pH).
   - Prohibits claiming satellite NDVI/NDWI/NDMI directly proves crop suitability.
   - Highlights data provenance, missing sources, and benchmark trial limitations.
4. **Resilient Production API**:
   - `POST /api/recommendations` endpoint with full OpenAPI documentation, input validation, clean 400/422/503 error handling, and zero fabricated fallbacks.
5. **Comprehensive Verification**:
   - 171 total automated tests passing (`test_recommendation.py`, `test_feature_engineering.py`, `test_weather.py`, `test_satellite.py`, `test_soil.py`, `test_model.py`, `test_data_pipeline.py`).

