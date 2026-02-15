# Integration and End-to-End Testing Guide

## Agri-Analytics Platform (Krishi Mitra / Mandi Mitra)

This guide provides comprehensive instructions for setting up, testing, and validating the backend API endpoints.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Database Initialization](#2-database-initialization)
3. [Starting the Development Server](#3-starting-the-development-server)
4. [API Endpoint Testing](#4-api-endpoint-testing)
5. [Postman Collection](#5-postman-collection)
6. [Swagger UI Testing](#6-swagger-ui-testing)
7. [End-to-End Test Scenarios](#7-end-to-end-test-scenarios)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

### 1.1 Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| PostgreSQL | 14+ | Primary database |
| PostGIS | 3.3+ | Geospatial queries |
| Redis | 7.0+ | Caching layer |
| Git | Latest | Version control |

### 1.2 Verify Installations

```bash
# Check Python version
python --version
# Expected: Python 3.11.x or higher

# Check PostgreSQL
psql --version
# Expected: psql (PostgreSQL) 14.x or higher

# Check Redis
redis-cli --version
# Expected: redis-cli 7.x.x

# Check PostGIS extension (after PostgreSQL installation)
psql -U postgres -c "SELECT PostGIS_Version();"
```

### 1.3 Environment Variables Setup

Copy the example environment file and configure it:

```bash
# Navigate to project root
cd /path/to/Aiforbharat

# Copy example env file
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# ============================================
# Application Settings
# ============================================
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ============================================
# Database Configuration
# ============================================
DB_USER=agri_user
DB_PASSWORD=agri_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agri_analytics

# Full database URL
DATABASE_URL=postgresql+asyncpg://agri_user:agri_password@localhost:5432/agri_analytics

# ============================================
# Redis Configuration
# ============================================
REDIS_URL=redis://localhost:6379/0
REDIS_PORT=6379

# ============================================
# Security Settings
# ============================================
SECRET_KEY=your-super-secret-key-for-testing-only-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# Feature Flags (for testing)
# ============================================
ENABLE_VOICE_QUERY=true
ENABLE_WHATSAPP_BOT=true
ENABLE_PRICE_ALERTS=true
```

### 1.4 Database Creation

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database user
CREATE USER agri_user WITH PASSWORD 'agri_password';

# Create database
CREATE DATABASE agri_analytics OWNER agri_user;

# Connect to the database
\c agri_analytics

# Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agri_analytics TO agri_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agri_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agri_user;

# Exit psql
\q
```

### 1.5 Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

---

## 2. Database Initialization

### 2.1 Run Alembic Migrations

```bash
# Navigate to backend directory
cd backend

# Initialize Alembic (if not already done)
alembic init alembic

# Generate migration (if needed)
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 2.2 Insert Sample Commodities

Execute the following SQL to insert sample commodities:

```sql
-- Connect to database
psql -U agri_user -d agri_analytics

-- Insert sample commodities
INSERT INTO commodities (name, category, unit, description, created_at, updated_at) VALUES
('Tomato', 'Vegetables', 'Quintal', 'Fresh red tomatoes', NOW(), NOW()),
('Onion', 'Vegetables', 'Quintal', 'Common onion variety', NOW(), NOW()),
('Potato', 'Vegetables', 'Quintal', 'Potato tubers', NOW(), NOW()),
('Wheat', 'Cereals', 'Quintal', 'Wheat grain', NOW(), NOW()),
('Rice', 'Cereals', 'Quintal', 'Basmati rice', NOW(), NOW()),
('Maize', 'Cereals', 'Quintal', 'Yellow maize', NOW(), NOW()),
('Sugarcane', 'Cash Crops', 'Quintal', 'Sugarcane stalks', NOW(), NOW()),
('Cotton', 'Cash Crops', 'Quintal', 'Raw cotton', NOW(), NOW()),
('Groundnut', 'Oilseeds', 'Quintal', 'Groundnut pods', NOW(), NOW()),
('Mustard', 'Oilseeds', 'Quintal', 'Mustard seeds', NOW(), NOW()),
('Brinjal', 'Vegetables', 'Quintal', 'Purple brinjal/eggplant', NOW(), NOW()),
('Cauliflower', 'Vegetables', 'Quintal', 'White cauliflower', NOW(), NOW()),
('Cabbage', 'Vegetables', 'Quintal', 'Green cabbage', NOW(), NOW()),
('Spinach', 'Leafy Vegetables', 'Quintal', 'Fresh spinach leaves', NOW(), NOW()),
('Green Chilli', 'Vegetables', 'Quintal', 'Green chillies', NOW(), NOW());
```

### 2.3 Insert Sample Mandis with Coordinates

```sql
-- Insert sample mandis with geospatial data
INSERT INTO mandis (name, state, district, latitude, longitude, location, market_type, pincode, contact_phone, is_active, created_at, updated_at) VALUES
-- Maharashtra
('Pune APMC', 'Maharashtra', 'Pune', 18.5204, 73.8567, ST_SetSRID(ST_MakePoint(73.8567, 18.5204), 4326), 'Regulated', '411001', '020-25530001', true, NOW(), NOW()),
('Mumbai Vashi', 'Maharashtra', 'Mumbai', 19.0760, 72.8777, ST_SetSRID(ST_MakePoint(72.8777, 19.0760), 4326), 'Regulated', '400703', '022-27890123', true, NOW(), NOW()),
('Nashik Market', 'Maharashtra', 'Nashik', 20.0059, 73.7910, ST_SetSRID(ST_MakePoint(73.7910, 20.0059), 4326), 'Regulated', '422001', '0253-2501234', true, NOW(), NOW()),
('Nagpur APMC', 'Maharashtra', 'Nagpur', 21.1458, 79.0882, ST_SetSRID(ST_MakePoint(79.0882, 21.1458), 4326), 'Regulated', '440001', '0712-2560456', true, NOW(), NOW()),
('Kolhapur Market', 'Maharashtra', 'Kolhapur', 16.7050, 74.2433, ST_SetSRID(ST_MakePoint(74.2433, 16.7050), 4326), 'Regulated', '416001', '0231-2650789', true, NOW(), NOW()),

-- Karnataka
('Bangalore KR Market', 'Karnataka', 'Bangalore', 12.9716, 77.5946, ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326), 'Regulated', '560002', '080-26701111', true, NOW(), NOW()),
('Mysore APMC', 'Karnataka', 'Mysore', 12.2958, 76.6394, ST_SetSRID(ST_MakePoint(76.6394, 12.2958), 4326), 'Regulated', '570001', '0821-2421234', true, NOW(), NOW()),
('Hubli Market', 'Karnataka', 'Hubli', 15.3647, 75.1240, ST_SetSRID(ST_MakePoint(75.1240, 15.3647), 4326), 'Regulated', '580020', '0836-2260456', true, NOW(), NOW()),

-- Gujarat
('Ahmedabad APMC', 'Gujarat', 'Ahmedabad', 23.0225, 72.5714, ST_SetSRID(ST_MakePoint(72.5714, 23.0225), 4326), 'Regulated', '380015', '079-25601234', true, NOW(), NOW()),
('Rajkot Market', 'Gujarat', 'Rajkot', 22.3039, 70.8022, ST_SetSRID(ST_MakePoint(70.8022, 22.3039), 4326), 'Regulated', '360001', '0281-2223456', true, NOW(), NOW()),
('Surat APMC', 'Gujarat', 'Surat', 21.1702, 72.8311, ST_SetSRID(ST_MakePoint(72.8311, 21.1702), 4326), 'Regulated', '395003', '0261-2478901', true, NOW(), NOW()),

-- Madhya Pradesh
('Indore APMC', 'Madhya Pradesh', 'Indore', 22.7196, 75.8577, ST_SetSRID(ST_MakePoint(75.8577, 22.7196), 4326), 'Regulated', '452001', '0731-2701234', true, NOW(), NOW()),
('Bhopal Market', 'Madhya Pradesh', 'Bhopal', 23.2599, 77.4126, ST_SetSRID(ST_MakePoint(77.4126, 23.2599), 4326), 'Regulated', '462001', '0755-2745678', true, NOW(), NOW()),

-- Punjab
('Ludhiana APMC', 'Punjab', 'Ludhiana', 30.9010, 75.8573, ST_SetSRID(ST_MakePoint(75.8573, 30.9010), 4326), 'Regulated', '141001', '0161-2701234', true, NOW(), NOW()),
('Amritsar Market', 'Punjab', 'Amritsar', 31.6340, 74.8723, ST_SetSRID(ST_MakePoint(74.8723, 31.6340), 4326), 'Regulated', '143001', '0183-2567890', true, NOW(), NOW()),

-- Haryana
('Karnal Market', 'Haryana', 'Karnal', 29.6857, 76.9905, ST_SetSRID(ST_MakePoint(76.9905, 29.6857), 4326), 'Regulated', '132001', '0184-2290123', true, NOW(), NOW()),
('Sonipat APMC', 'Haryana', 'Sonipat', 28.9929, 77.0295, ST_SetSRID(ST_MakePoint(77.0295, 28.9929), 4326), 'Regulated', '131001', '0130-2234567', true, NOW(), NOW()),

-- Uttar Pradesh
('Lucknow APMC', 'Uttar Pradesh', 'Lucknow', 26.8467, 80.9462, ST_SetSRID(ST_MakePoint(80.9462, 26.8467), 4326), 'Regulated', '226001', '0522-2630123', true, NOW(), NOW()),
('Kanpur Market', 'Uttar Pradesh', 'Kanpur', 26.4499, 80.3319, ST_SetSRID(ST_MakePoint(80.3319, 26.4499), 4326), 'Regulated', '208001', '0512-2304567', true, NOW(), NOW()),
('Agra APMC', 'Uttar Pradesh', 'Agra', 27.1767, 78.0081, ST_SetSRID(ST_MakePoint(78.0081, 27.1767), 4326), 'Regulated', '282001', '0562-2850123', true, NOW(), NOW()),

-- Rajasthan
('Jaipur APMC', 'Rajasthan', 'Jaipur', 26.9124, 75.7873, ST_SetSRID(ST_MakePoint(75.7873, 26.9124), 4326), 'Regulated', '302001', '0141-2701234', true, NOW(), NOW()),
('Jodhpur Market', 'Rajasthan', 'Jodhpur', 26.2389, 73.0243, ST_SetSRID(ST_MakePoint(73.0243, 26.2389), 4326), 'Regulated', '342001', '0291-2645678', true, NOW(), NOW());
```

### 2.4 Insert Sample Price Data (30 Days)

```sql
-- Insert sample price data for the last 30 days
-- This script generates realistic price variations

DO $$
DECLARE
    rec_date DATE;
    commodity_rec RECORD;
    mandi_rec RECORD;
    base_price DECIMAL(10,2);
    min_p DECIMAL(10,2);
    max_p DECIMAL(10,2);
    modal_p DECIMAL(10,2);
    arrival INT;
BEGIN
    -- Loop through last 30 days
    FOR rec_date IN SELECT CURRENT_DATE - i FROM generate_series(0, 29) i LOOP
        -- Loop through commodities
        FOR commodity_rec IN SELECT id, name FROM commodities WHERE is_active = true LOOP
            -- Set base price based on commodity
            CASE commodity_rec.name
                WHEN 'Tomato' THEN base_price := 1500 + (RANDOM() * 500)::DECIMAL;
                WHEN 'Onion' THEN base_price := 1200 + (RANDOM() * 400)::DECIMAL;
                WHEN 'Potato' THEN base_price := 800 + (RANDOM() * 300)::DECIMAL;
                WHEN 'Wheat' THEN base_price := 2200 + (RANDOM() * 300)::DECIMAL;
                WHEN 'Rice' THEN base_price := 2800 + (RANDOM() * 400)::DECIMAL;
                WHEN 'Maize' THEN base_price := 1800 + (RANDOM() * 300)::DECIMAL;
                WHEN 'Sugarcane' THEN base_price := 350 + (RANDOM() * 100)::DECIMAL;
                WHEN 'Cotton' THEN base_price := 5500 + (RANDOM() * 800)::DECIMAL;
                WHEN 'Groundnut' THEN base_price := 4500 + (RANDOM() * 600)::DECIMAL;
                WHEN 'Mustard' THEN base_price := 4200 + (RANDOM() * 500)::DECIMAL;
                WHEN 'Brinjal' THEN base_price := 1200 + (RANDOM() * 400)::DECIMAL;
                WHEN 'Cauliflower' THEN base_price := 1400 + (RANDOM() * 400)::DECIMAL;
                WHEN 'Cabbage' THEN base_price := 1000 + (RANDOM() * 300)::DECIMAL;
                WHEN 'Spinach' THEN base_price := 800 + (RANDOM() * 300)::DECIMAL;
                WHEN 'Green Chilli' THEN base_price := 3000 + (RANDOM() * 1000)::DECIMAL;
                ELSE base_price := 1500 + (RANDOM() * 500)::DECIMAL;
            END CASE;
            
            -- Loop through mandis
            FOR mandi_rec IN SELECT id FROM mandis WHERE is_active = true LOOP
                -- Add regional variation (±15%)
                base_price := base_price * (0.85 + RANDOM() * 0.30);
                
                -- Calculate min, max, modal prices
                min_p := base_price * 0.90;
                max_p := base_price * 1.10;
                modal_p := base_price;
                
                -- Random arrival quantity (50-500 quintals)
                arrival := (50 + (RANDOM() * 450))::INT;
                
                -- Insert price record
                INSERT INTO prices (mandi_id, commodity_id, price_date, min_price, max_price, modal_price, arrival_qty, created_at, updated_at)
                VALUES (mandi_rec.id, commodity_rec.id, rec_date, min_p, max_p, modal_p, arrival, NOW(), NOW())
                ON CONFLICT (mandi_id, commodity_id, price_date) DO NOTHING;
            END LOOP;
        END LOOP;
    END LOOP;
END $$;
```

### 2.5 Create Sample Test User

```sql
-- Insert a sample test user
-- Password hash for 'TestPassword123!' using bcrypt
INSERT INTO users (phone_number, email, full_name, password_hash, preferred_language, state, district, is_active, is_verified, created_at, updated_at)
VALUES (
    '9876543210',
    'testuser@agribharat.com',
    'Test Farmer',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.qO.1BoWBPfGKWe',  -- 'TestPassword123!'
    'en',
    'Maharashtra',
    'Pune',
    true,
    true,
    NOW(),
    NOW()
);
```

---

## 3. Starting the Development Server

### 3.1 Start Redis Server

```bash
# On Windows (if installed as service)
redis-server --service-start

# Or run directly
redis-server

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

### 3.2 Start FastAPI Server

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment if not already active
# On Windows:
..\.venv\Scripts\activate
# On Linux/Mac:
source ../.venv/bin/activate

# Start the server with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with more detailed logging
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 3.3 Verify Server is Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "Agri-Analytics API", "version": "1.0.0"}

# Check root endpoint
curl http://localhost:8000/

# Expected response:
# {"name": "Agri-Analytics API", "version": "1.0.0", "docs": "/docs", "health": "/health"}
```

### 3.4 Access API Documentation

| Documentation | URL | Description |
|---------------|-----|-------------|
| Swagger UI | http://localhost:8000/docs | Interactive API documentation |
| ReDoc | http://localhost:8000/redoc | Alternative documentation view |
| OpenAPI JSON | http://localhost:8000/openapi.json | Raw OpenAPI specification |

---

## 4. API Endpoint Testing

### 4.1 Authentication Endpoints

#### Register New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9123456789",
    "email": "newuser@example.com",
    "full_name": "New Test User",
    "password": "SecurePassword123!",
    "preferred_language": "en",
    "state": "Maharashtra",
    "district": "Pune"
  }'
```

**Expected Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Login with Phone and Password

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "password": "TestPassword123!"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Request OTP

```bash
curl -X POST "http://localhost:8000/api/v1/auth/otp/request" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "purpose": "login"
  }'
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "message": "OTP sent successfully. Code: 123456"
}
```

#### Verify OTP and Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "otp_code": "123456"
  }'
```

#### Get Current User Profile (Protected)

```bash
# Replace YOUR_ACCESS_TOKEN with the actual token from login
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "phone_number": "9876543210",
  "email": "testuser@agribharat.com",
  "full_name": "Test Farmer",
  "preferred_language": "en",
  "state": "Maharashtra",
  "district": "Pune",
  "is_active": true,
  "is_verified": true,
  "whatsapp_id": null,
  "last_login": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Refresh Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh?refresh_token=YOUR_REFRESH_TOKEN"
```

---

### 4.2 Commodity Endpoints

#### List All Commodities

```bash
curl -X GET "http://localhost:8000/api/v1/commodities?page=1&page_size=20"
```

**Expected Response:**
```json
{
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 1,
      "name": "Tomato",
      "category": "Vegetables",
      "unit": "Quintal",
      "description": "Fresh red tomatoes",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    },
    ...
  ]
}
```

#### Filter Commodities by Category

```bash
curl -X GET "http://localhost:8000/api/v1/commodities?category=Vegetables"
```

#### Search Commodities

```bash
curl -X GET "http://localhost:8000/api/v1/commodities?search=tomato"
```

#### Get Commodity by ID

```bash
curl -X GET "http://localhost:8000/api/v1/commodities/1"
```

**Expected Response:**
```json
{
  "id": 1,
  "name": "Tomato",
  "category": "Vegetables",
  "unit": "Quintal",
  "description": "Fresh red tomatoes",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Commodity Categories

```bash
curl -X GET "http://localhost:8000/api/v1/commodities/categories"
```

**Expected Response:**
```json
["Vegetables", "Cereals", "Cash Crops", "Oilseeds", "Leafy Vegetables"]
```

---

### 4.3 Mandi Endpoints

#### List All Mandis

```bash
curl -X GET "http://localhost:8000/api/v1/mandis?page=1&page_size=20"
```

**Expected Response:**
```json
{
  "total": 22,
  "page": 1,
  "page_size": 20,
  "total_pages": 2,
  "items": [
    {
      "id": 1,
      "name": "Pune APMC",
      "state": "Maharashtra",
      "district": "Pune",
      "latitude": 18.5204,
      "longitude": 73.8567,
      "market_type": "Regulated",
      "pincode": "411001",
      "contact_phone": "020-25530001",
      "is_active": true
    },
    ...
  ]
}
```

#### Filter Mandis by State

```bash
curl -X GET "http://localhost:8000/api/v1/mandis?state=Maharashtra"
```

#### Filter Mandis by District

```bash
curl -X GET "http://localhost:8000/api/v1/mandis?state=Maharashtra&district=Pune"
```

#### Search Mandis

```bash
curl -X GET "http://localhost:8000/api/v1/mandis?search=Pune"
```

#### Get Mandi by ID

```bash
curl -X GET "http://localhost:8000/api/v1/mandis/1"
```

#### Get All States

```bash
curl -X GET "http://localhost:8000/api/v1/mandis/states"
```

**Expected Response:**
```json
["Maharashtra", "Karnataka", "Gujarat", "Madhya Pradesh", "Punjab", "Haryana", "Uttar Pradesh", "Rajasthan"]
```

#### Get Districts by State

```bash
curl -X GET "http://localhost:8000/api/v1/mandis/states/Maharashtra/districts"
```

**Expected Response:**
```json
["Pune", "Mumbai", "Nashik", "Nagpur", "Kolhapur"]
```

#### Find Nearby Mandis (PostGIS Geospatial Query)

```bash
curl -X POST "http://localhost:8000/api/v1/mandis/nearby" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 18.5204,
    "longitude": 73.8567,
    "radius_km": 500,
    "limit": 10
  }'
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "name": "Pune APMC",
    "state": "Maharashtra",
    "district": "Pune",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "distance_km": 0.0
  },
  {
    "id": 3,
    "name": "Nashik Market",
    "state": "Maharashtra",
    "district": "Nashik",
    "latitude": 20.0059,
    "longitude": 73.7910,
    "distance_km": 155.2
  },
  ...
]
```

---

### 4.4 Price Endpoints

#### Get Price History

```bash
# Get prices for commodity_id=1 (Tomato) for last 30 days
curl -X GET "http://localhost:8000/api/v1/prices?commodity_id=1&days=30"
```

**Expected Response:**
```json
{
  "total": 660,
  "page": 1,
  "page_size": 100,
  "total_pages": 7,
  "items": [
    {
      "id": 1,
      "mandi_id": 1,
      "commodity_id": 1,
      "price_date": "2024-01-15",
      "min_price": 1350.00,
      "max_price": 1650.00,
      "modal_price": 1500.00,
      "arrival_qty": 250
    },
    ...
  ]
}
```

#### Get Prices with Filters

```bash
# Filter by commodity, mandi, and date range
curl -X GET "http://localhost:8000/api/v1/prices?commodity_id=1&mandi_id=1&start_date=2024-01-01&end_date=2024-01-15"
```

#### Get Current Prices by Commodity

```bash
curl -X GET "http://localhost:8000/api/v1/prices/current/commodity/1"
```

**Expected Response:**
```json
[
  {
    "id": 660,
    "mandi_id": 1,
    "commodity_id": 1,
    "commodity_name": "Tomato",
    "mandi_name": "Pune APMC",
    "state": "Maharashtra",
    "district": "Pune",
    "price_date": "2024-01-15",
    "min_price": 1350.00,
    "max_price": 1650.00,
    "modal_price": 1500.00,
    "arrival_qty": 250
  },
  ...
]
```

#### Get Current Prices by Mandi

```bash
curl -X GET "http://localhost:8000/api/v1/prices/current/mandi/1"
```

#### Get Price Trend

```bash
curl -X GET "http://localhost:8000/api/v1/prices/trend/1?mandi_id=1&days=90"
```

**Expected Response:**
```json
[
  {
    "date": "2024-01-15",
    "avg_price": 1500.00,
    "min_price": 1350.00,
    "max_price": 1650.00,
    "total_arrival": 5000
  },
  {
    "date": "2024-01-14",
    "avg_price": 1480.00,
    "min_price": 1330.00,
    "max_price": 1630.00,
    "total_arrival": 4800
  },
  ...
]
```

#### Compare Prices Across Mandis

```bash
curl -X POST "http://localhost:8000/api/v1/prices/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "commodity_id": 1,
    "mandi_ids": [1, 2, 3, 4, 5]
  }'
```

#### Get Top Gainers

```bash
curl -X GET "http://localhost:8000/api/v1/prices/gainers?limit=10"
```

#### Get Top Losers

```bash
curl -X GET "http://localhost:8000/api/v1/prices/losers?limit=10"
```

---

### 4.5 Forecast Endpoints

#### Get Price Forecast

```bash
# Get 7-day forecast for Tomato at Pune APMC
curl -X GET "http://localhost:8000/api/v1/forecasts/1/1?horizon_days=7&include_explanation=true"
```

**Expected Response:**
```json
{
  "commodity_id": 1,
  "commodity_name": "Tomato",
  "mandi_id": 1,
  "mandi_name": "Pune APMC",
  "current_price": 1500.00,
  "forecasted_price": 1580.00,
  "price_change": 80.00,
  "price_change_pct": 5.33,
  "horizon_days": 7,
  "confidence_lower": 1520.00,
  "confidence_upper": 1640.00,
  "confidence_level": 0.95,
  "trend": "upward",
  "explanation": {
    "top_features": [
      {"feature": "historical_trend", "importance": 0.35, "direction": "positive"},
      {"feature": "seasonality", "importance": 0.25, "direction": "positive"},
      {"feature": "arrival_volume", "importance": 0.20, "direction": "negative"}
    ],
    "summary": "Prices expected to increase due to seasonal demand and reduced arrivals."
  },
  "forecast_date": "2024-01-15"
}
```

#### Get Multi-Horizon Forecasts

```bash
curl -X GET "http://localhost:8000/api/v1/forecasts/1/1/multi-horizon?horizons=1,3,7,14,30"
```

**Expected Response:**
```json
{
  "commodity_id": 1,
  "commodity_name": "Tomato",
  "mandi_id": 1,
  "mandi_name": "Pune APMC",
  "current_price": 1500.00,
  "forecasts": [
    {
      "horizon_days": 1,
      "forecasted_price": 1505.00,
      "confidence_lower": 1480.00,
      "confidence_upper": 1530.00
    },
    {
      "horizon_days": 3,
      "forecasted_price": 1520.00,
      "confidence_lower": 1470.00,
      "confidence_upper": 1570.00
    },
    {
      "horizon_days": 7,
      "forecasted_price": 1580.00,
      "confidence_lower": 1520.00,
      "confidence_upper": 1640.00
    },
    {
      "horizon_days": 14,
      "forecasted_price": 1620.00,
      "confidence_lower": 1500.00,
      "confidence_upper": 1740.00
    },
    {
      "horizon_days": 30,
      "forecasted_price": 1550.00,
      "confidence_lower": 1380.00,
      "confidence_upper": 1720.00
    }
  ],
  "overall_trend": "upward"
}
```

#### Batch Forecasts

```bash
curl -X POST "http://localhost:8000/api/v1/forecasts/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {"commodity_id": 1, "mandi_id": 1, "horizon_days": 7},
    {"commodity_id": 1, "mandi_id": 2, "horizon_days": 7},
    {"commodity_id": 2, "mandi_id": 1, "horizon_days": 7}
  ]'
```

#### Get Best Selling Opportunities

```bash
curl -X GET "http://localhost:8000/api/v1/forecasts/1/best-opportunities?mandi_ids=1,2,3,4,5,6,7,8,9,10&horizon_days=7&min_price_change=5.0&limit=5"
```

---

### 4.6 ETL Endpoints

#### Trigger Manual Price Scraping

```bash
curl -X POST "http://localhost:8000/api/v1/etl/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "state": "Maharashtra",
    "commodity": "Tomato"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Scraping job started",
  "job_id": "scrape_20240115_143000"
}
```

#### Get ETL Job Status

```bash
curl -X GET "http://localhost:8000/api/v1/etl/status?job_id=scrape_20240115_143000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "job_id": "scrape_20240115_143000",
  "status": "completed",
  "started_at": "2024-01-15T14:30:00Z",
  "completed_at": "2024-01-15T14:32:30Z",
  "records_processed": 450,
  "records_inserted": 420,
  "records_updated": 30,
  "errors": []
}
```

---

## 5. Postman Collection

### 5.1 Import the Collection

Create a file named `agri_analytics_postman_collection.json` and import it into Postman:

```json
{
  "info": {
    "name": "Agri-Analytics API",
    "description": "Collection for testing Agri-Analytics Platform APIs",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "access_token",
      "value": ""
    },
    {
      "key": "refresh_token",
      "value": ""
    }
  ],
  "event": [
    {
      "listen": "prerequest",
      "script": {
        "type": "text/javascript",
        "exec": [
          "// Auto-refresh token if expired",
          "if (pm.environment.get('token_expires_at') && ",
          "    Date.now() > pm.environment.get('token_expires_at')) {",
          "    console.log('Token expired, need to refresh');",
          "}"
        ]
      }
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Register User",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phone_number\": \"9123456789\",\n  \"email\": \"test@example.com\",\n  \"full_name\": \"Test User\",\n  \"password\": \"TestPassword123!\",\n  \"preferred_language\": \"en\",\n  \"state\": \"Maharashtra\",\n  \"district\": \"Pune\"\n}"
            },
            "url": "{{base_url}}/api/v1/auth/register"
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "pm.test('Status code is 201', () => pm.response.to.have.status(201));",
                  "const json = pm.response.json();",
                  "pm.environment.set('access_token', json.access_token);",
                  "pm.environment.set('refresh_token', json.refresh_token);",
                  "pm.environment.set('token_expires_at', Date.now() + (json.expires_in * 1000));"
                ]
              }
            }
          ]
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"phone_number\": \"9876543210\",\n  \"password\": \"TestPassword123!\"\n}"
            },
            "url": "{{base_url}}/api/v1/auth/login"
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "type": "text/javascript",
                "exec": [
                  "pm.test('Status code is 200', () => pm.response.to.have.status(200));",
                  "const json = pm.response.json();",
                  "pm.environment.set('access_token', json.access_token);",
                  "pm.environment.set('refresh_token', json.refresh_token);",
                  "pm.environment.set('token_expires_at', Date.now() + (json.expires_in * 1000));"
                ]
              }
            }
          ]
        },
        {
          "name": "Get Current User",
          "request": {
            "method": "GET",
            "header": [],
            "url": "{{base_url}}/api/v1/auth/me"
          }
        },
        {
          "name": "Refresh Token",
          "request": {
            "method": "POST",
            "header": [],
            "url": {
              "raw": "{{base_url}}/api/v1/auth/refresh?refresh_token={{refresh_token}}",
              "query": [{"key": "refresh_token", "value": "{{refresh_token}}"}]
            }
          }
        }
      ]
    },
    {
      "name": "Commodities",
      "item": [
        {
          "name": "List Commodities",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/commodities"
          }
        },
        {
          "name": "Get Commodity by ID",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/commodities/1"
          }
        },
        {
          "name": "Get Categories",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/commodities/categories"
          }
        }
      ]
    },
    {
      "name": "Mandis",
      "item": [
        {
          "name": "List Mandis",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/mandis"
          }
        },
        {
          "name": "Get Mandi by ID",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/mandis/1"
          }
        },
        {
          "name": "Find Nearby Mandis",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"latitude\": 18.5204,\n  \"longitude\": 73.8567,\n  \"radius_km\": 200,\n  \"limit\": 10\n}"
            },
            "url": "{{base_url}}/api/v1/mandis/nearby"
          }
        },
        {
          "name": "Get States",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/mandis/states"
          }
        }
      ]
    },
    {
      "name": "Prices",
      "item": [
        {
          "name": "Get Price History",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/prices?commodity_id=1&days=30"
          }
        },
        {
          "name": "Get Current Prices by Commodity",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/prices/current/commodity/1"
          }
        },
        {
          "name": "Get Price Trend",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/prices/trend/1?days=90"
          }
        },
        {
          "name": "Compare Prices",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"commodity_id\": 1,\n  \"mandi_ids\": [1, 2, 3, 4, 5]\n}"
            },
            "url": "{{base_url}}/api/v1/prices/compare"
          }
        }
      ]
    },
    {
      "name": "Forecasts",
      "item": [
        {
          "name": "Get Price Forecast",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/forecasts/1/1?horizon_days=7&include_explanation=true"
          }
        },
        {
          "name": "Get Multi-Horizon Forecast",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/v1/forecasts/1/1/multi-horizon"
          }
        },
        {
          "name": "Batch Forecasts",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "[\n  {\"commodity_id\": 1, \"mandi_id\": 1, \"horizon_days\": 7},\n  {\"commodity_id\": 2, \"mandi_id\": 1, \"horizon_days\": 7}\n]"
            },
            "url": "{{base_url}}/api/v1/forecasts/batch"
          }
        }
      ]
    },
    {
      "name": "Health",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/health"
          }
        }
      ]
    }
  ]
}
```

### 5.2 Environment Variables

Create a Postman environment with these variables:

| Variable | Initial Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `access_token` | (empty) | Set automatically after login |
| `refresh_token` | (empty) | Set automatically after login |
| `token_expires_at` | (empty) | Timestamp for token expiry |

---

## 6. Swagger UI Testing

### 6.1 Access Swagger UI

1. Start the development server
2. Open browser and navigate to: http://localhost:8000/docs

### 6.2 Authorize Requests

1. Click the **Authorize** button at the top right of the Swagger UI
2. In the dialog that appears, enter your JWT token in the format: `Bearer YOUR_ACCESS_TOKEN`
3. Click **Authorize**
4. Click **Close**

### 6.3 Test an Endpoint

1. Click on any endpoint to expand it
2. Click **Try it out**
3. Fill in the required parameters
4. Click **Execute**
5. View the response below

### 6.4 Example: Testing Login Flow

1. Navigate to **POST /api/v1/auth/login**
2. Click **Try it out**
3. Enter the request body:
   ```json
   {
     "phone_number": "9876543210",
     "password": "TestPassword123!"
   }
   ```
4. Click **Execute**
5. Copy the `access_token` from the response
6. Click **Authorize** at the top
7. Enter: `Bearer <copied_access_token>`
8. Now you can test protected endpoints

---

## 7. End-to-End Test Scenarios

### Scenario 1: User Registration → Login → Fetch Commodities → Get Prices

```bash
#!/bin/bash
# e2e_test_scenario_1.sh

echo "=== E2E Test Scenario 1: User Flow ==="

# Step 1: Register a new user
echo -e "\n[Step 1] Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9988776655",
    "email": "e2etest@example.com",
    "full_name": "E2E Test User",
    "password": "E2ETestPassword123!",
    "preferred_language": "en",
    "state": "Maharashtra",
    "district": "Pune"
  }')

echo "Register Response: $REGISTER_RESPONSE"

# Extract access token
ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "ERROR: Failed to get access token"
    exit 1
fi

echo "Access Token: ${ACCESS_TOKEN:0:50}..."

# Step 2: Get user profile
echo -e "\n[Step 2] Getting user profile..."
PROFILE_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Profile Response: $PROFILE_RESPONSE"

# Step 3: List commodities
echo -e "\n[Step 3] Fetching commodities..."
COMMODITIES_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/commodities?page=1&page_size=5")

echo "Commodities Response: $COMMODITIES_RESPONSE"

# Extract first commodity ID
COMMODITY_ID=$(echo $COMMODITIES_RESPONSE | jq -r '.items[0].id')
echo "Selected Commodity ID: $COMMODITY_ID"

# Step 4: Get prices for the commodity
echo -e "\n[Step 4] Fetching prices for commodity $COMMODITY_ID..."
PRICES_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/prices?commodity_id=$COMMODITY_ID&days=7")

echo "Prices Response: $PRICES_RESPONSE"

# Verify response
TOTAL_PRICES=$(echo $PRICES_RESPONSE | jq -r '.total')
echo -e "\n[Result] Total price records found: $TOTAL_PRICES"

if [ "$TOTAL_PRICES" -gt 0 ]; then
    echo "✅ E2E Test Scenario 1: PASSED"
else
    echo "❌ E2E Test Scenario 1: FAILED"
fi
```

### Scenario 2: Create Forecast → Verify Response Structure

```bash
#!/bin/bash
# e2e_test_scenario_2.sh

echo "=== E2E Test Scenario 2: Forecast Flow ==="

# Step 1: Get a commodity and mandi
echo -e "\n[Step 1] Getting commodity and mandi IDs..."
COMMODITY_ID=$(curl -s "http://localhost:8000/api/v1/commodities" | jq -r '.items[0].id')
MANDI_ID=$(curl -s "http://localhost:8000/api/v1/mandis" | jq -r '.items[0].id')

echo "Commodity ID: $COMMODITY_ID"
echo "Mandi ID: $MANDI_ID"

# Step 2: Get forecast
echo -e "\n[Step 2] Getting price forecast..."
FORECAST_RESPONSE=$(curl -s -X GET \
  "http://localhost:8000/api/v1/forecasts/$COMMODITY_ID/$MANDI_ID?horizon_days=7&include_explanation=true")

echo "Forecast Response: $FORECAST_RESPONSE"

# Step 3: Verify response structure
echo -e "\n[Step 3] Verifying response structure..."

# Check required fields
HAS_COMMODITY_ID=$(echo $FORECAST_RESPONSE | jq 'has("commodity_id")')
HAS_MANDI_ID=$(echo $FORECAST_RESPONSE | jq 'has("mandi_id")')
HAS_FORECAST=$(echo $FORECAST_RESPONSE | jq 'has("forecasted_price")')
HAS_CONFIDENCE=$(echo $FORECAST_RESPONSE | jq 'has("confidence_lower")')
HAS_TREND=$(echo $FORECAST_RESPONSE | jq 'has("trend")')

echo "Has commodity_id: $HAS_COMMODITY_ID"
echo "Has mandi_id: $HAS_MANDI_ID"
echo "Has forecasted_price: $HAS_FORECAST"
echo "Has confidence bounds: $HAS_CONFIDENCE"
echo "Has trend: $HAS_TREND"

# Step 4: Get multi-horizon forecast
echo -e "\n[Step 4] Getting multi-horizon forecast..."
MULTI_RESPONSE=$(curl -s -X GET \
  "http://localhost:8000/api/v1/forecasts/$COMMODITY_ID/$MANDI_ID/multi-horizon?horizons=1,3,7,14,30")

echo "Multi-Horizon Response: $MULTI_RESPONSE"

# Verify
FORECAST_COUNT=$(echo $MULTI_RESPONSE | jq '.forecasts | length')
echo "Number of forecasts: $FORECAST_COUNT"

if [ "$HAS_COMMODITY_ID" == "true" ] && [ "$HAS_FORECAST" == "true" ] && [ "$FORECAST_COUNT" -ge 3 ]; then
    echo "✅ E2E Test Scenario 2: PASSED"
else
    echo "❌ E2E Test Scenario 2: FAILED"
fi
```

### Scenario 3: Trigger ETL → Check Status → Verify New Data

```bash
#!/bin/bash
# e2e_test_scenario_3.sh

echo "=== E2E Test Scenario 3: ETL Flow ==="

# Step 1: Login to get token
echo -e "\n[Step 1] Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "password": "TestPassword123!"}')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access Token: ${ACCESS_TOKEN:0:50}..."

# Step 2: Get current price count
echo -e "\n[Step 2] Getting current price count..."
BEFORE_COUNT=$(curl -s "http://localhost:8000/api/v1/prices?commodity_id=1&days=1" | jq -r '.total')
echo "Prices before ETL: $BEFORE_COUNT"

# Step 3: Trigger ETL job
echo -e "\n[Step 3] Triggering ETL job..."
ETL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/etl/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"state": "Maharashtra", "commodity": "Tomato"}')

echo "ETL Response: $ETL_RESPONSE"

JOB_ID=$(echo $ETL_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Step 4: Check job status (poll until complete)
echo -e "\n[Step 4] Checking job status..."
for i in {1..10}; do
    STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/etl/status?job_id=$JOB_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
    echo "Attempt $i: Status = $STATUS"
    
    if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
        break
    fi
    
    sleep 2
done

echo "Final Status Response: $STATUS_RESPONSE"

# Step 5: Verify new data
echo -e "\n[Step 5] Verifying new data..."
AFTER_COUNT=$(curl -s "http://localhost:8000/api/v1/prices?commodity_id=1&days=1" | jq -r '.total')
echo "Prices after ETL: $AFTER_COUNT"

RECORDS_PROCESSED=$(echo $STATUS_RESPONSE | jq -r '.records_processed')
echo "Records processed: $RECORDS_PROCESSED"

if [ "$STATUS" == "completed" ] && [ "$RECORDS_PROCESSED" -gt 0 ]; then
    echo "✅ E2E Test Scenario 3: PASSED"
else
    echo "❌ E2E Test Scenario 3: FAILED"
fi
```

---

## 8. Troubleshooting

### 8.1 Common Errors and Solutions

#### Database Connection Issues

**Error:** `connection to server at "localhost" (::1), port 5432 failed`

**Solutions:**
```bash
# Check if PostgreSQL is running
# On Windows:
net start postgresql-x64-14

# On Linux:
sudo systemctl status postgresql

# Verify connection parameters
psql -U agri_user -d agri_analytics -h localhost

# Check pg_hba.conf for authentication settings
# Location: C:\Program Files\PostgreSQL\14\data\pg_hba.conf (Windows)
# Or: /etc/postgresql/14/main/pg_hba.conf (Linux)

# Ensure this line exists:
# host    all    all    127.0.0.1/32    md5
```

**Error:** `FATAL: database "agri_analytics" does not exist`

**Solution:**
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE agri_analytics OWNER agri_user;"
```

#### Redis Connection Issues

**Error:** `redis.exceptions.ConnectionError: Error 10061 connecting to localhost:6379`

**Solutions:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis server
# On Windows (as service):
redis-server --service-start

# Or directly:
redis-server

# Check Redis configuration
redis-cli INFO server
```

#### PostGIS Extension Issues

**Error:** `function st_makepoint(double precision, double precision) does not exist`

**Solution:**
```sql
-- Connect to database
psql -U agri_user -d agri_analytics

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify
SELECT PostGIS_Version();
```

#### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**
```bash
# Ensure you're in the backend directory
cd backend

# Ensure virtual environment is activated
# On Windows:
..\.venv\Scripts\activate
# On Linux/Mac:
source ../.venv/bin/activate

# Set PYTHONPATH
# On Windows:
set PYTHONPATH=%cd%
# On Linux/Mac:
export PYTHONPATH=$PWD

# Run from project root
cd ..
python -m backend.app.main
```

**Error:** `ImportError: cannot import name 'AsyncSession' from 'sqlalchemy.ext.asyncio'`

**Solution:**
```bash
# Ensure SQLAlchemy 2.0+ is installed
pip install --upgrade sqlalchemy

# Verify version
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
# Should be 2.0.x
```

#### JWT Token Issues

**Error:** `401 Unauthorized - Invalid or expired token`

**Solutions:**
```bash
# Get a new token via login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "password": "TestPassword123!"}'

# Or refresh the token
curl -X POST "http://localhost:8000/api/v1/auth/refresh?refresh_token=YOUR_REFRESH_TOKEN"

# Check token expiration in .env
# ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### CORS Issues

**Error:** `Access to XMLHttpRequest at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution:**
```env
# Update .env file
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:3003
```

### 8.2 Debug Mode

Enable debug mode for detailed error messages:

```env
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### 8.3 Checking Logs

```bash
# View uvicorn logs in console
uvicorn app.main:app --reload --log-level debug

# Check PostgreSQL logs
# Windows: C:\Program Files\PostgreSQL\14\data\log\
# Linux: /var/log/postgresql/

# Check Redis logs
redis-cli INFO stats
```

### 8.4 Database Queries for Debugging

```sql
-- Check commodities
SELECT * FROM commodities LIMIT 5;

-- Check mandis
SELECT id, name, state, district, latitude, longitude FROM mandis LIMIT 5;

-- Check prices
SELECT p.id, c.name as commodity, m.name as mandi, p.price_date, p.modal_price
FROM prices p
JOIN commodities c ON p.commodity_id = c.id
JOIN mandis m ON p.mandi_id = m.id
ORDER BY p.price_date DESC
LIMIT 10;

-- Check users
SELECT id, phone_number, email, full_name, is_active, is_verified FROM users;

-- Check PostGIS
SELECT ST_AsText(location) FROM mandis LIMIT 3;
```

---

## Quick Reference

### API Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/auth/register | Register new user | No |
| POST | /api/v1/auth/login | Login with phone/password | No |
| POST | /api/v1/auth/otp/request | Request OTP | No |
| POST | /api/v1/auth/otp/verify | Verify OTP | No |
| GET | /api/v1/auth/me | Get current user | Yes |
| GET | /api/v1/commodities | List commodities | No |
| GET | /api/v1/commodities/{id} | Get commodity | No |
| GET | /api/v1/mandis | List mandis | No |
| POST | /api/v1/mandis/nearby | Find nearby mandis | No |
| GET | /api/v1/prices | Get price history | No |
| GET | /api/v1/prices/trend/{id} | Get price trend | No |
| GET | /api/v1/forecasts/{commodity_id}/{mandi_id} | Get forecast | No |
| POST | /api/v1/forecasts/batch | Batch forecasts | No |
| POST | /api/v1/etl/scrape | Trigger scraping | Yes |
| GET | /api/v1/etl/status | Get ETL status | Yes |
| GET | /health | Health check | No |

### Default Test Credentials

| Field | Value |
|-------|-------|
| Phone | 9876543210 |
| Password | TestPassword123! |
| Email | testuser@agribharat.com |

---

*Last Updated: February 2024*
*Version: 1.0.0*
