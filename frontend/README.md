# AgriSense AI — Farmer Dashboard & Frontend Integration (Phase 10)

Welcome to the **AgriSense AI Farmer Dashboard**, a precision-agriculture web application built with **React**, **TypeScript**, **Vite**, **Tailwind CSS v4**, **Leaflet OpenStreetMap**, and **Recharts**.

The dashboard connects directly with the AgriSense AI FastAPI backend (`http://127.0.0.1:8000`) to present live environmental telemetry, benchmark crop recommendations, FAO-grounded crop advisories, and water requirements.

---

## 🌾 Design Philosophy & Scientific Integrity

1. **No Fabricated Telemetry**: Environmental observations (weather, soil, satellite) are rendered only when retrieved from active APIs or verified regional presets. When unavailable, clear contextual notices ("Data unavailable — Connect to backend") are displayed rather than placeholders or zeroes.
2. **Strict Terminology**: Model recommendations use the exact backend terminology `probability_estimate` and `confidence` percentages. They are never labeled as "crop suitability percentages" or "guaranteed harvest success".
3. **Evidence-Based Advisory**: Compatibility assessments adhere to backend FAO ECOCROP rules and FAO-56 irrigation estimates. The frontend does not invent suitability scores or arbitrary weighting formulas.
4. **Interactive Geospatial Pinpoint**: The Leaflet map provides a 500m analysis buffer around coordinates, clearly disclaiming that point buffers do not represent surveyed legal farm boundaries.

---

## 🛠️ Technology Stack

- **Core**: React 19, TypeScript, Vite 8
- **Styling**: Tailwind CSS v4 with custom precision-agriculture forest green tokens
- **Interactive Mapping**: Leaflet with OpenStreetMap tiles (`react-leaflet` not required; clean native Leaflet lifecycle integration)
- **Data Visualizations**: Recharts (radar charts, bar charts, custom gauges)
- **Icons**: Lucide React
- **Routing**: React Router DOM (v7)
- **HTTP Client**: Native Fetch API with centralized typed client and timeout abort controllers

---

## 📁 Frontend Architecture

```text
frontend/
├── .env                  # Local dev environment configuration
├── .env.example          # Environment variable template
├── index.html            # Entry HTML with Inter typography
├── package.json          # Dependencies and npm scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration (port 5173, chunk limits)
├── src/
│   ├── main.tsx          # React application root
│   ├── App.tsx           # Router and application layout
│   ├── index.css         # Global styles and Tailwind CSS v4 directives
│   ├── types/            # Strict TypeScript definitions matching backend Pydantic models
│   │   ├── common.ts     # FarmLocation, ApiState, AgriculturalPresets
│   │   ├── weather.ts    # WeatherResponse, WeatherCurrent, WeatherDaily
│   │   ├── satellite.ts  # SatelliteResponse, Indices (NDVI, NDWI, NDMI)
│   │   ├── soil.ts       # SoilResponse, SoilLayerData (ISRIC SoilGrids)
│   │   ├── recommendation.ts # RecommendationResponse, RankedCropItem
│   │   └── advisory.ts   # FarmAdvisoryResponse, Compatibility, WaterAdvisory
│   ├── api/              # Centralized typed API service layer
│   │   ├── client.ts     # Base fetch wrapper with error & timeout handling
│   │   ├── health.ts     # GET /health & root GET /
│   │   ├── weather.ts    # GET /api/weather
│   │   ├── satellite.ts  # GET /api/satellite
│   │   ├── soil.ts       # GET /api/soil
│   │   ├── recommendations.ts # POST /api/recommendations
│   │   └── advisory.ts   # POST /api/advisory
│   ├── context/          # Global farm state management
│   │   ├── FarmContextBase.ts # Context definition & interface
│   │   ├── FarmContext.tsx    # FarmProvider implementation
│   │   └── useFarm.ts         # Custom consumer hook
│   ├── components/       # Modular, reusable UI components
│   │   ├── layout/       # Sidebar, Header, Layout shell
│   │   ├── common/       # StatCard, StatusBadge, LoadingSkeleton, ErrorAlert, DisclaimerBox
│   │   ├── map/          # FarmMapSelector (Leaflet OSM canvas, manual inputs, presets)
│   │   ├── dashboard/    # WeatherWidget, SoilWidget, SatelliteWidget
│   │   ├── recommendation/ # RecommendationForm, RecommendationCard
│   │   └── advisory/     # CropAdvisoryCard, WaterAdvisoryCard, RiskFlagList, VariableBreakdown
│   └── pages/            # View pages
│       ├── DashboardPage.tsx       # Main overview with quick scouting & summaries
│       ├── FarmMapPage.tsx         # Dedicated Leaflet map & telemetry workbench
│       ├── RecommendationsPage.tsx # Form + top-K recommendation results
│       ├── AdvisoryPage.tsx        # FAO-56 water & environmental compatibility audits
│       ├── MethodologyPage.tsx     # Scientific citations, FAO formulas, provenance
│       └── SettingsPage.tsx        # Backend connectivity diagnostics & endpoint switcher
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **npm**: v9.0.0 or higher
- **Backend**: AgriSense AI FastAPI backend running on `http://127.0.0.1:8000`

### 1. Installation

From the project root:

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure the API base URL matches your FastAPI server:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will start at: `http://localhost:5173`

### 4. Build for Production

```bash
npm run build
```

Performs strict TypeScript validation (`tsc -b`) and bundles optimized production assets via Vite into `frontend/dist/`.

### 5. Linting

```bash
npm run lint
```

Runs the ultra-fast Oxlint linter to verify strict React 19 rules, JSX syntax, and hooks dependencies.

---

## 🔗 Backend Communication & CORS

The frontend communicates with the following FastAPI endpoints:

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check & system status |
| `/api/weather` | `GET` | Open-Meteo live weather telemetry |
| `/api/soil` | `GET` | ISRIC SoilGrids 2.0 depth profiles |
| `/api/satellite` | `GET` | Sentinel-2 / Earth Engine vegetation indices |
| `/api/recommendations` | `POST` | Top-K crop recommendations from benchmark model |
| `/api/advisory` | `POST` | FAO ECOCROP compatibility & FAO-56 water requirements |

### Backend CORS

The backend in `backend/app/main.py` is configured with `CORSMiddleware` supporting:
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

---

## 🧪 Scientific Disclaimer

The AgriSense AI farmer dashboard presents benchmark machine learning predictions and FAO agronomic guidance for exploratory and decision-support purposes. It does not replace certified professional agronomic advisory or local soil laboratory tests.
