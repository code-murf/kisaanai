- # KisaanAI - Design Document

## 1. Executive Summary

This document outlines the technical architecture, system design, and implementation strategy for KisaanAI - a comprehensive agricultural analytics platform. The design emphasizes scalability, accessibility, and real-time performance while addressing the unique challenges of serving rural Indian farmers.

## 2. System Architecture Overview

### 2.1 High-Level Architecture

KisaanAI follows a microservices architecture pattern with the following key components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Web App  │  │Mobile App│  │ WhatsApp │  │Voice API │   │
│  │(Next.js) │  │(React N.)│  │   Bot    │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  API Gateway   │
                    │  (Rate Limit,  │
                    │   Auth, Cache) │
                    └───────┬────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ Auth │ │Price │ │Mandi │ │Voice │ │Credit│ │Crop  │   │
│  │Service│ │Svc  │ │Svc  │ │Agent │ │Svc  │ │Doctor│   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Redis   │  │  MinIO   │  │TimescaleDB│  │
│  │(+PostGIS)│  │  Cache   │  │(Objects) │  │(TimeSeries)│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                    ML & Analytics Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ XGBoost  │  │  Prophet │  │   SHAP   │  │  Disease │   │
│  │Forecaster│  │Seasonality│  │Explainer │  │Detection │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```


### 2.2 Architecture Principles

1. **Microservices**: Independent, loosely coupled services for scalability
2. **API-First**: All functionality exposed through well-documented REST APIs
3. **Event-Driven**: Asynchronous communication for non-blocking operations
4. **Cloud-Native**: Containerized services with orchestration support
5. **Data-Driven**: ML models at the core of decision-making

## 3. Component Design

### 3.1 Frontend Architecture

#### 3.1.1 Web Application (Next.js)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state
- **Data Fetching**: React Query for server state
- **Maps**: Leaflet with custom tile layers
- **Charts**: Recharts for data visualization
- **Animations**: Framer Motion for smooth transitions

**Key Pages**:
- Dashboard: Personalized insights and quick actions
- Price Forecasts: Interactive charts and predictions
- Mandi Finder: Map-based mandi discovery
- Crop Doctor: Image upload and disease detection
- KisaanCredit: Credit scoring and loan applications
- Profile: User settings and preferences

#### 3.1.2 Mobile Application (React Native)
- **Framework**: React Native with Expo
- **Navigation**: React Navigation
- **Offline Support**: AsyncStorage + Redux Persist
- **Voice**: Expo Speech API
- **Camera**: Expo Camera for crop disease detection
- **Location**: Expo Location for geolocation


### 3.2 Backend Services

#### 3.2.1 API Gateway
- **Technology**: Kong or AWS API Gateway
- **Responsibilities**:
  - Request routing and load balancing
  - Authentication and authorization
  - Rate limiting (100 req/min per user)
  - Request/response transformation
  - API versioning
  - Caching layer (Redis)

#### 3.2.2 Authentication Service
- **Technology**: FastAPI + JWT
- **Features**:
  - Phone number-based authentication
  - OTP verification via SMS gateway
  - JWT token generation and validation
  - Role-based access control (RBAC)
  - Session management
  - OAuth2 integration for future social login

**Database Schema**:
```sql
users (
  id UUID PRIMARY KEY,
  phone VARCHAR(15) UNIQUE,
  name VARCHAR(100),
  language VARCHAR(10),
  district VARCHAR(50),
  village VARCHAR(50),
  role VARCHAR(20),
  created_at TIMESTAMP,
  last_login TIMESTAMP
)
```


#### 3.2.3 Price Forecasting Service
- **Technology**: FastAPI + ONNX Runtime
- **ML Models**:
  - XGBoost for short-term predictions (7-14 days)
  - Prophet for seasonal patterns (30+ days)
  - Ensemble model combining both approaches

**API Endpoints**:
```
GET  /api/v1/forecasts/{commodity}?days=7&district=xyz
POST /api/v1/forecasts/batch
GET  /api/v1/forecasts/{commodity}/explanation
GET  /api/v1/forecasts/accuracy-metrics
```

**Database Schema**:
```sql
price_history (
  id SERIAL PRIMARY KEY,
  commodity_id INT,
  mandi_id INT,
  date DATE,
  min_price DECIMAL(10,2),
  max_price DECIMAL(10,2),
  modal_price DECIMAL(10,2),
  arrivals INT
)

forecasts (
  id SERIAL PRIMARY KEY,
  commodity_id INT,
  district VARCHAR(50),
  forecast_date DATE,
  predicted_price DECIMAL(10,2),
  confidence_lower DECIMAL(10,2),
  confidence_upper DECIMAL(10,2),
  model_version VARCHAR(20),
  created_at TIMESTAMP
)
```


#### 3.2.4 Mandi Service
- **Technology**: FastAPI + PostGIS
- **Features**:
  - Geospatial queries for nearby mandis
  - Route optimization using OpenRouteService
  - Net profit calculation (Price - Transport Cost)
  - Real-time mandi status updates

**API Endpoints**:
```
GET  /api/v1/mandis?lat=28.7&lon=77.1&radius=50
GET  /api/v1/mandis/{id}
GET  /api/v1/mandis/recommend?commodity=wheat&location=xyz
POST /api/v1/mandis/route-optimize
```

**Database Schema**:
```sql
mandis (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  district VARCHAR(50),
  state VARCHAR(50),
  location GEOGRAPHY(POINT),
  contact VARCHAR(15),
  operating_hours JSONB,
  facilities TEXT[]
)

mandi_commodities (
  mandi_id INT,
  commodity_id INT,
  is_active BOOLEAN,
  PRIMARY KEY (mandi_id, commodity_id)
)
```


#### 3.2.5 Voice Agent Service
- **Technology**: FastAPI + OpenAI Whisper + Coqui TTS
- **Features**:
  - Speech-to-Text (STT) in multiple languages
  - Natural Language Understanding (NLU)
  - Intent classification and entity extraction
  - Text-to-Speech (TTS) responses
  - Context-aware conversation management

**Supported Intents**:
- `get_price`: "Aaj aaloo ka bhaav kya hai?"
- `get_forecast`: "Agale hafte tomato ka price kya hoga?"
- `find_mandi`: "Mere paas kaun sa mandi hai?"
- `weather_query`: "Aaj mausam kaisa rahega?"
- `crop_advice`: "Gehun ki bimari ka ilaaj?"

**API Endpoints**:
```
POST /api/v1/voice/transcribe
POST /api/v1/voice/query
POST /api/v1/voice/synthesize
GET  /api/v1/voice/session/{session_id}
```

#### 3.2.6 Crop Doctor Service
- **Technology**: FastAPI + PyTorch + ResNet50
- **Features**:
  - Image-based disease detection
  - Treatment recommendations
  - Severity assessment
  - Historical disease tracking

**Supported Crops**: Wheat, Rice, Potato, Tomato, Cotton, Sugarcane, etc.

**API Endpoints**:
```
POST /api/v1/crop-doctor/detect
GET  /api/v1/crop-doctor/diseases/{crop_type}
GET  /api/v1/crop-doctor/treatment/{disease_id}
POST /api/v1/crop-doctor/feedback
```


#### 3.2.7 KisaanCredit Service
- **Technology**: FastAPI + Scikit-learn
- **Features**:
  - Credit score calculation
  - Loan product recommendations
  - Application processing
  - Repayment tracking
  - Integration with partner NBFCs

**Credit Scoring Factors**:
- Land ownership and size
- Historical crop yields
- Market transaction history
- Repayment history
- Weather risk assessment

**API Endpoints**:
```
POST /api/v1/credit/calculate-score
GET  /api/v1/credit/loan-products
POST /api/v1/credit/apply
GET  /api/v1/credit/applications/{user_id}
POST /api/v1/credit/repayment
```

**Database Schema**:
```sql
credit_profiles (
  user_id UUID PRIMARY KEY,
  credit_score INT,
  land_size DECIMAL(10,2),
  annual_income DECIMAL(12,2),
  risk_category VARCHAR(20),
  last_updated TIMESTAMP
)

loan_applications (
  id UUID PRIMARY KEY,
  user_id UUID,
  amount DECIMAL(12,2),
  purpose VARCHAR(100),
  status VARCHAR(20),
  partner_id INT,
  applied_at TIMESTAMP,
  approved_at TIMESTAMP
)
```


### 3.3 Data Pipeline Architecture

#### 3.3.1 ETL Pipeline (Prefect)
- **Orchestration**: Prefect for workflow management
- **Schedule**: Daily runs at 6 AM IST
- **Data Sources**:
  - Agmarknet scraper (BeautifulSoup + Selenium)
  - IMD weather API
  - Sentinel-2 satellite imagery
  - OpenStreetMap data

**Pipeline Stages**:
1. **Extract**: Fetch data from multiple sources
2. **Transform**: Clean, validate, and enrich data
3. **Load**: Store in PostgreSQL and TimescaleDB
4. **Trigger**: Initiate model retraining if needed

#### 3.3.2 Data Quality Framework
- **Validation Rules**:
  - Price range checks (min < modal < max)
  - Temporal consistency (no sudden 10x jumps)
  - Geospatial validation (coordinates within India)
  - Completeness checks (required fields present)

- **Monitoring**:
  - Data freshness alerts
  - Anomaly detection
  - Source availability tracking
  - Quality score dashboard

