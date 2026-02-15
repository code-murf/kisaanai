# Competition Implementation Plan: Agri-Analytics Platform

## Goal Description
Build a scalable, high-imact Agricultural Analytics Platform to predict commodity prices, recommend optimal mandis, and provide accessible advisory services (Voice/WhatsApp) for Indian farmers.

## User Review Required
> [!IMPORTANT]
> **Data Access Policy:** Confirm if scraping Agmarknet is allowed by competition rules. If not, we must rely solely on Open Government Data API (which may have latency).
> **WhatsApp API Cost:** The WhatsApp Business API has per-conversation costs. For the competition, we'll use a sandbox or trial.

## Proposed Architecture & Changes

### 1. Data Ingestion & Storage (Data Engineering Squad)
-   **Database:** PostgreSQL (with PostGIS extension) for relational & geospatial data.
-   **Object Store:** MinIO (local S3 compatible) or AWS S3 for raw data (images, huge CSVs).
-   **Pipeline:** Prefect or Dagster for orchestration.
-   **Sources:**
    -   `Agmarknet`: Python `requests` + `BeautifulSoup` scraper / API client.
    -   `IMD/Weather`: IMD Gridded Data downloader (Python `imdl` library or custom script).
    -   `Sentinel-2`: `sentinehub-py` or `rasterio` for processing .SAFE files.

### 2. Machine Learning Pipeline (ML Squad)
-   **Feature Store:** Feast (optional, or simple SQL tables for competition).
-   **Models:**
    -   **Price Forecasting:** Gradient Boosting (XGBoost/LightGBM) + Prophet for seasonality.
    -   **Crop Health:** NDVI calculation from Sentinel-2 (simple scalar value per district/mandi catchment).
-   **Training:**
    -   Automated retraining pipeline triggered weekly.
    -   Model Registry: MLflow for experiment tracking.

### 3. Backend Services (Backend Squad)
-   **API Framework:** FastAPI (Python).
-   **Microservices:**
    -   `auth-service`: JWT authentication.
    -   `commodity-service`: Price history & metadata.
    -   `forecast-service`: Serving ML predictions (ONNX runtime for speed).
    -   `router-service`: Optimization logic (Price - Transport Cost).
-   **WhatsApp Bot:** Integration with Twilio/Meta API webhook.

### 4. Frontend & Accessibility (Frontend Squad)
-   **Web Dashboard:** Next.js (React) + Tailwind CSS.
    -   Interactive Map (Leaflet/Mapbox GL JS).
    -   Price charts (Recharts).
-   **Voice Interface:**
    -   Browser-native Web Speech API (basic) or server-side Whisper (advanced).

## Verification Plan

### Automated Tests
-   **Backend:** `pytest` for all API endpoints and logic.
    -   `pytest tests/api/test_forecast.py`
-   **ML:** Unit tests for data transformation functions.
    -   `pytest tests/ml/test_features.py` (e.g., ensure NDVI is between -1 and 1).
-   **End-to-End:** Playwright for critical user flows (Login -> Select Crop -> View Forecast).

### Manual Verification
-   **Accuracy Check:** Compare predicted prices vs actuals for held-out test set (last 2 weeks).
-   **UX Test:** "Grandmother Test" - Can a non-tech savvy person get a price using the Voice feature?
-   **Load Test:** Locust script to simulate 100 concurrent users hitting the API.
