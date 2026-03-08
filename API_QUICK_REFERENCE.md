# API Quick Reference

> **KisaanAI API Endpoints - Quick Reference Guide**

**Base URL**: `http://13.53.186.103/api/v1`

---

## 🔐 Authentication

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "phone": "+919876543210",
  "name": "Farmer Name"
}

Response: 200 OK
{
  "user_id": 1,
  "phone": "+919876543210",
  "name": "Farmer Name"
}
```

### Send OTP
```http
POST /auth/otp/send
Content-Type: application/json

{
  "phone": "+919876543210"
}

Response: 200 OK
{
  "message": "OTP sent successfully",
  "otp_id": "uuid-here"
}
```

### Verify OTP & Get Token
```http
POST /auth/otp/verify
Content-Type: application/json

{
  "phone": "+919876543210",
  "otp": "123456"
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 🎤 Voice Assistant (AWS Bedrock + CloudWatch)

### Process Voice Query
```http
POST /voice/query
Content-Type: multipart/form-data

Form Data:
- file: audio.wav (audio/wav, audio/mp3, audio/webm, audio/m4a)
- language: hi-IN (default: hi-IN)
- session_id: optional-uuid (for barge-in support)
- lat: 28.7041 (optional)
- lon: 77.1025 (optional)

Response: 200 OK
{
  "query": "गेहूं की कीमत क्या है?",
  "response": "गेहूं की वर्तमान कीमत ₹2500 प्रति क्विंटल है...",
  "audio": "base64_encoded_audio_data",
  "language": "hi-IN",
  "session_id": "uuid-here"
}
```

### Process Text Query (Web Speech Recognition)
```http
POST /voice/text
Content-Type: application/json

{
  "text": "What is the current wheat price?",
  "language": "en-IN",
  "lat": 28.7041,
  "lon": 77.1025
}

Response: 200 OK
{
  "query": "What is the current wheat price?",
  "response": "The current wheat price is ₹2500 per quintal...",
  "audio": "base64_encoded_audio_data",
  "language": "en-IN"
}
```

### Cancel Voice Request (Barge-in)
```http
POST /voice/cancel
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
- session_id: uuid-here

Response: 200 OK
{
  "cancelled": true,
  "session_id": "uuid-here",
  "message": "Request cancelled successfully"
}
```

### Create Voice Session
```http
POST /voice/session
Authorization: Bearer <token>

Response: 200 OK
{
  "session_id": "uuid-here",
  "user_id": "1",
  "message": "Session created successfully"
}
```

### Get Voice Stats
```http
GET /voice/stats

Response: 200 OK
{
  "active_sessions": 5,
  "active_requests": 3
}
```

---

## 🌾 Crop Disease Detection (AWS S3 + Bedrock Vision)

### Diagnose Plant Disease
```http
POST /diseases/diagnose
Content-Type: multipart/form-data

Form Data:
- file: crop_image.jpg (image/jpeg, image/png)

Response: 200 OK
{
  "disease_name": "Leaf Blight",
  "confidence": 0.87,
  "treatment": "Apply fungicide containing mancozeb or chlorothalonil. Spray every 7-10 days...",
  "severity": "medium",
  "image_url": "https://kisaanai-uploads.s3.ap-south-1.amazonaws.com/crops/2026/03/08/abc123_crop_image.jpg",
  "s3_key": "crops/2026/03/08/abc123_crop_image.jpg",
  "timestamp": "2026-03-08T10:30:00"
}
```

**Note**: `image_url` is a presigned S3 URL valid for 1 hour

---

## 📊 Price Forecasting (ML + SHAP)

### Get Price Forecast
```http
GET /forecasts/{commodity_id}/{mandi_id}?horizon_days=7

Example: GET /forecasts/1/1?horizon_days=7

Response: 200 OK
{
  "predicted_price": 2500.50,
  "confidence_lower": 2400.00,
  "confidence_upper": 2600.00,
  "horizon_days": 7,
  "commodity": {
    "id": 1,
    "name": "Wheat"
  },
  "mandi": {
    "id": 1,
    "name": "Azadpur",
    "district": "Delhi"
  },
  "explanation": {
    "shap_values": [...],
    "feature_importance": {
      "historical_price": 0.45,
      "season": 0.25,
      "weather": 0.20,
      "demand": 0.10
    }
  }
}
```

**Query Parameters**:
- `horizon_days`: 7, 14, or 30 (default: 7)

---

## 🗺️ Mandi Routing

### Get Mandi Recommendations
```http
POST /routing/recommend
Content-Type: application/json

{
  "commodity_id": 1,
  "user_lat": 28.7041,
  "user_lon": 77.1025,
  "quantity_kg": 1000,
  "transport_cost_per_km": 5.0
}

Response: 200 OK
[
  {
    "mandi": {
      "id": 1,
      "name": "Azadpur",
      "district": "Delhi",
      "state": "Delhi",
      "lat": 28.7041,
      "lon": 77.1025
    },
    "price": 2500.00,
    "distance_km": 15.5,
    "transport_cost": 77.50,
    "net_profit": 2422.50,
    "rank": 1
  },
  {
    "mandi": {
      "id": 2,
      "name": "Kota",
      "district": "Kota",
      "state": "Rajasthan",
      "lat": 25.2138,
      "lon": 75.8648
    },
    "price": 2600.00,
    "distance_km": 450.0,
    "transport_cost": 2250.00,
    "net_profit": 350.00,
    "rank": 2
  }
]
```

---

## 📈 Commodities & Mandis

### Get All Commodities
```http
GET /commodities

Response: 200 OK
[
  {
    "id": 1,
    "name": "Wheat",
    "unit": "quintal",
    "category": "cereals"
  },
  {
    "id": 2,
    "name": "Rice",
    "unit": "quintal",
    "category": "cereals"
  },
  {
    "id": 3,
    "name": "Cotton",
    "unit": "quintal",
    "category": "cash_crops"
  }
]
```

### Get All Mandis
```http
GET /mandis

Response: 200 OK
[
  {
    "id": 1,
    "name": "Azadpur",
    "district": "Delhi",
    "state": "Delhi",
    "lat": 28.7041,
    "lon": 77.1025
  },
  {
    "id": 2,
    "name": "Kota",
    "district": "Kota",
    "state": "Rajasthan",
    "lat": 25.2138,
    "lon": 75.8648
  }
]
```

### Get Current Prices
```http
GET /prices/current?commodity_id=1&mandi_id=1&limit=10

Response: 200 OK
[
  {
    "id": 1,
    "commodity": {
      "id": 1,
      "name": "Wheat",
      "unit": "quintal"
    },
    "mandi": {
      "id": 1,
      "name": "Azadpur",
      "district": "Delhi",
      "state": "Delhi"
    },
    "modal_price": 2500.00,
    "min_price": 2400.00,
    "max_price": 2600.00,
    "date": "2026-03-08"
  }
]
```

**Query Parameters**:
- `commodity_id`: Filter by commodity (optional)
- `mandi_id`: Filter by mandi (optional)
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)

---

## 🌤️ Weather

### Get Weather Forecast
```http
GET /weather/forecast?lat=28.7041&lon=77.1025&days=7

Response: 200 OK
[
  {
    "date": "2026-03-08",
    "condition": "Partly Cloudy",
    "temp_max": 32.5,
    "temp_min": 18.2,
    "humidity": 65,
    "rainfall_mm": 0.0,
    "wind_speed_kmh": 15.5,
    "advisory": "Good conditions for irrigation. Monitor for pests."
  },
  {
    "date": "2026-03-09",
    "condition": "Sunny",
    "temp_max": 34.0,
    "temp_min": 19.5,
    "humidity": 60,
    "rainfall_mm": 0.0,
    "wind_speed_kmh": 12.0,
    "advisory": "Ideal weather for field work."
  }
]
```

**Query Parameters**:
- `lat`: Latitude (required)
- `lon`: Longitude (required)
- `days`: Number of days (1-7, default: 3)

---

## 📰 News

### Get Agricultural News
```http
GET /news?limit=10&offset=0&category=policy

Response: 200 OK
[
  {
    "id": 1,
    "title": "New MSP announced for wheat",
    "content": "Government announces minimum support price of ₹2500 per quintal...",
    "category": "policy",
    "published_at": "2026-03-08T10:00:00",
    "source": "PIB",
    "url": "https://pib.gov.in/..."
  },
  {
    "id": 2,
    "title": "Monsoon forecast for 2026",
    "content": "IMD predicts normal monsoon with 98% of long-term average...",
    "category": "weather",
    "published_at": "2026-03-07T15:30:00",
    "source": "IMD",
    "url": "https://imd.gov.in/..."
  }
]
```

**Query Parameters**:
- `limit`: Number of results (default: 10)
- `offset`: Pagination offset (default: 0)
- `category`: Filter by category (policy, weather, market, technology)

---

## 👥 Community

### Get Community Posts
```http
GET /community/posts?limit=10&offset=0

Response: 200 OK
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "name": "Farmer Name",
      "phone": "+919876543210"
    },
    "content": "Looking for advice on wheat disease...",
    "created_at": "2026-03-08T10:00:00",
    "likes": 5,
    "comments": 3
  }
]
```

### Create Post
```http
POST /community/posts
Content-Type: application/json
Authorization: Bearer <token>

{
  "content": "Looking for advice on wheat disease..."
}

Response: 201 Created
{
  "id": 1,
  "user_id": 1,
  "content": "Looking for advice on wheat disease...",
  "created_at": "2026-03-08T10:00:00"
}
```

---

## 🏥 Health Check

### Check API Health
```http
GET /health

Response: 200 OK
{
  "status": "healthy",
  "service": "KisaanAI API",
  "version": "1.0.0"
}
```

---

## 🔧 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "errors": [
    {
      "field": "commodity_id",
      "message": "Field required",
      "type": "missing"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## 📊 Rate Limiting

- **Rate Limit**: 100 requests per minute per IP
- **Headers**:
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: 95
  - `X-RateLimit-Reset`: 1678291200

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## 🔗 CORS

**Allowed Origins**: `*` (all origins)

**Allowed Methods**: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

**Allowed Headers**: `*` (all headers)

---

## 📝 Notes

1. **Authentication**: Most endpoints require JWT token in `Authorization: Bearer <token>` header
2. **Content-Type**: Use `application/json` for JSON requests, `multipart/form-data` for file uploads
3. **Timestamps**: All timestamps are in ISO 8601 format (UTC)
4. **Pagination**: Use `limit` and `offset` query parameters
5. **AWS Integration**:
   - Voice API uses AWS Bedrock (Claude 3) and CloudWatch
   - Disease API uses AWS S3 (image storage) and Bedrock Vision
   - All APIs tracked with CloudWatch metrics

---

**Live API**: http://13.53.186.103/api/v1  
**Documentation**: http://13.53.186.103/docs (when DEBUG=True)  
**Health Check**: http://13.53.186.103/health
