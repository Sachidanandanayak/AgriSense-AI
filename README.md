# AgriSense AI 🌾🛰️

**Satellite & AI-Powered Crop Suitability and Farm Advisory Platform**

---

> **Current Development Status:** **Phase 4 — Weather Data Integration**

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

- **6. Machine Learning Engine**  
  Trained on multi-dimensional agro-climatic datasets to predict crop suitability classifications, yield potential tiers, and viability scores.

- **7. Crop Recommendation & Advisory System**  
  Generates ranked recommendations alongside expected growing periods, water budgets, and optimal sowing windows.

- **8. Environmental Risk Analysis**  
  Evaluates environmental vulnerability—such as late-season heat stress, flood vulnerability, or prolonged dry spells—and provides mitigation advisories.

- **9. Farmer Dashboard (Frontend)**  
  A clean, intuitive, and responsive web interface designed to present complex geospatial insights through clear visual cards, charts, maps, and straightforward advisory summaries.

---

## 🛠️ Planned Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & API** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **Data Processing & ML** | NumPy, Pandas, Scikit-learn, XGBoost / LightGBM, Joblib |
| **Geospatial & Satellite** | Earth Engine API / Sentinel Hub / Planetary Computer, Rasterio, GeoPandas |
| **Weather APIs** | Open-Meteo / NASA POWER / NOAA APIs |
| **Frontend** | Modern Web Framework (React / Next.js / Vite), Responsive CSS |
| **Storage & Caching** | PostgreSQL / PostGIS (Planned), Redis (Planned) |
| **Testing & CI** | Pytest, Flake8 / Ruff |

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
│   │   │   └── routes/          # Versioned route endpoints
│   │   ├── core/                # App configuration, settings, logging
│   │   ├── models/              # Internal domain models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic (weather, satellite, crop analysis)
│   │   └── utils/               # Shared helpers and formatters
│   ├── tests/                   # Backend automated test suite
│   ├── data/
│   │   ├── raw/                 # Raw agricultural and spatial data
│   │   └── processed/           # Feature-engineered datasets
│   ├── ml/
│   │   ├── datasets/            # Training/evaluation datasets
│   │   ├── notebooks/           # Exploratory data analysis & model experiments
│   │   ├── models/              # Serialized trained model weights/artifacts
│   │   └── scripts/             # Training, evaluation, and export pipelines
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Backend-specific documentation
├── frontend/                    # Web dashboard (to be built in upcoming phases)
├── .gitignore                   # Version control ignore rules
└── README.md                    # Project documentation
```

---

## 🚀 Current Milestone

> **Phase 4 — Weather Data Integration**  
> Established resilient, decoupled meteorological data ingestion service interfacing with Open-Meteo, normalizing observations (temperature, humidity, precipitation, wind speed) into unified Pydantic schemas under `/api/weather` with full test isolation.
