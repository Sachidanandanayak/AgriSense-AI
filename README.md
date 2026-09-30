# AgriSense AI 🌾🛰️

**Satellite & AI-Powered Crop Suitability and Farm Advisory Platform**

---

> **Current Development Status:** **Phase 7 — Multi-Source Feature Engineering**

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

- **8. Crop Recommendation & Advisory System**  
  Generates ranked recommendations alongside expected growing periods, water budgets, and optimal sowing windows.

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
│   │   │   └── routes/          # Versioned route endpoints (weather, satellite, soil)
│   │   ├── core/                # App configuration, settings, logging
│   │   ├── models/              # Internal domain models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic services
│   │   │   ├── weather_service.py
│   │   │   ├── satellite_service.py
│   │   │   ├── soil_service.py
│   │   │   ├── soil_provider.py
│   │   │   └── feature_engineering/ # Multi-source feature orchestration (Phase 7)
│   │   │       ├── __init__.py
│   │   │       ├── schemas.py      # Unified multi-source contracts
│   │   │       ├── normalizer.py   # Source normalization
│   │   │       ├── builder.py      # Feature engineering builder
│   │   │       └── validators.py   # Spatial/temporal/leakage validation
│   │   └── utils/               # Shared helpers and formatters
│   ├── tests/                   # Backend automated test suite (136 tests)


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

## 🚀 Current Milestone: Phase 7 — Multi-Source Feature Engineering

> **Phase 7 Objective:**  
> Create a clean, reproducible, and leakage-free feature-engineering architecture that unifies:
> 1. **Historical agricultural data** (N, P, K, pH, rainfall, temperature, humidity)
> 2. **Weather data** (2m air temperature, relative humidity, precipitation, 10m wind speed)
> 3. **Satellite-derived indicators** (Sentinel-2 NDVI, NDWI, NDMI, scene counts, cloud thresholds)
> 4. **Soil properties** (ISRIC SoilGrids pH, clay, sand, silt %, SOC, bulk density, CEC, Nitrogen)
>
> into a standardized, deterministic multi-source feature representation (`MultiSourceObservation` / `MultiSourceFeatureVector`).

### Critical Architectural Boundary & Anti-Fabrication Rule
> **"The current benchmark agricultural dataset lacks the geospatial and temporal keys required to legitimately join live weather, satellite, and soil observations. Therefore, Phase 7 creates the multi-source feature contract and alignment infrastructure without fabricating historical environmental observations."**

- **Zero Synthetic Alignment**: Historical rows are never assigned arbitrary coordinates, today's weather, or SoilGrids predictions.
- **Strict Leakage Prevention**: Ground-truth target labels (`crop_label`) are strictly isolated from ML prediction feature vectors.
- **Scientifically Defensible Derived Ratios**: Nutrient ratios ($N/P$, $N/K$, $P/K$) are protected against division-by-zero, returning `None` instead of synthetic zeros or averages.
- **Model Preservation**: The existing Phase 3 Random Forest model artifact, metrics, and report remain 100% immutable and un-retrained.

