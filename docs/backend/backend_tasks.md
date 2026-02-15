# Backend & ML Squad Tasks

## Phase 1: Foundation & Data (Week 1)
- [ ] **Infrastructure Setup**
    - [ ] Initialize FastAPI project with Docker Compose.
    - [ ] Set up PostgreSQL with PostGIS extension.
    - [ ] Configure MinIO/S3 for object storage.
- [ ] **Data Ingestion Pipeline**
    - [ ] Write Python script to fetch daily data from Agmarknet API/Scraper.
    - [ ] Implement data cleaning & normalization (Pandas).
    - [ ] Store processed data in PostgreSQL (TimescaleDB hypertable recommended).
- [ ] **Database Schema**
    - [ ] Design tables for `Commodities`, `Mandis` (with Lat/Lon), `Prices`, `Weather`.

## Phase 2: Core Logic & ML (Week 2)
- [ ] **ML Modeling (Price Forecasting)**
    - [ ] Train baseline XGBoost model on historical price data.
    - [ ] Implement Temporal Fusion Transformer (TFT) for long-term trends.
    - [ ] Expose model via ONNX runtime or TorchServe.
- [ ] **API Development**
    - [ ] `GET /mandis`: List all mandis with geolocation.
    - [ ] `GET /predict`: Return price forecast for Commodity X at Mandi Y.
    - [ ] `POST /route`: Calculate optimal mandi based on (Price - Transport Cost).

## Phase 3: "Winning Features" (Week 3)
- [ ] **WhatsApp Bot Integration**
    - [ ] Set up Twilio Sandbox / Meta Cloud API.
    - [ ] Implement webhook to parse user messages ("Potato Price").
    - [ ] Connect webhook to `predict` service.
- [ ] **Voice Processing**
    - [ ] Integrate Bhashini ASR API header generation.
    - [ ] Implement logical flow: Audio -> Text -> Intent -> Data -> Audio Response.

## Phase 4: Testing & Optimization (Week 4)
- [ ] Load testing with Locust (1000 forecasts/min).
- [ ] API Security audit (Rate limiting, Input validation).
