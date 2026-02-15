"""
Pydantic schemas for API request/response models.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ==================== Base Schemas ====================

class BaseResponse(BaseModel):
    """Base response schema."""
    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel):
    """Generic success response."""
    status: str = "success"
    message: Optional[str] = None
    data: Optional[dict] = None


class ErrorDetail(BaseModel):
    """Error detail schema."""
    detail: str
    code: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema."""
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    preferred_language: str = Field(default="en", max_length=10)
    state: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    preferred_language: Optional[str] = Field(default=None, max_length=10)
    state: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)


class UserResponse(BaseResponse):
    """Schema for user response."""
    id: int
    phone_number: str
    email: Optional[str]
    full_name: Optional[str]
    preferred_language: str
    state: Optional[str]
    district: Optional[str]
    is_active: bool
    is_verified: bool
    whatsapp_id: Optional[str]
    last_login: Optional[datetime]
    created_at: datetime


class UserListResponse(PaginatedResponse):
    """Schema for paginated user list."""
    items: List[UserResponse]


# ==================== Auth Schemas ====================

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Schema for login request."""
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: Optional[str] = Field(default=None)


class OTPRequest(BaseModel):
    """Schema for OTP request."""
    phone_number: str = Field(..., min_length=10, max_length=20)
    purpose: str = Field(default="login", max_length=50)


class OTPVerifyRequest(BaseModel):
    """Schema for OTP verification."""
    phone_number: str = Field(..., min_length=10, max_length=20)
    otp_code: str = Field(..., min_length=4, max_length=10)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


# ==================== Commodity Schemas ====================

class CommodityBase(BaseModel):
    """Base commodity schema."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(default="Quintal", max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)


class CommodityCreate(CommodityBase):
    """Schema for creating a commodity."""
    pass


class CommodityUpdate(BaseModel):
    """Schema for updating a commodity."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class CommodityResponse(BaseResponse):
    """Schema for commodity response."""
    id: int
    name: str
    category: str
    unit: str
    description: Optional[str]
    is_active: bool
    created_at: datetime


class CommodityListResponse(PaginatedResponse):
    """Schema for paginated commodity list."""
    items: List[CommodityResponse]


# ==================== Mandi Schemas ====================

class MandiBase(BaseModel):
    """Base mandi schema."""
    name: str = Field(..., min_length=1, max_length=255)
    state: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    market_type: str = Field(default="Regulated", max_length=50)
    pincode: Optional[str] = Field(default=None, max_length=10)
    contact_phone: Optional[str] = Field(default=None, max_length=20)


class MandiCreate(MandiBase):
    """Schema for creating a mandi."""
    pass


class MandiUpdate(BaseModel):
    """Schema for updating a mandi."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    state: Optional[str] = Field(default=None, min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, min_length=1, max_length=100)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    market_type: Optional[str] = Field(default=None, max_length=50)
    pincode: Optional[str] = Field(default=None, max_length=10)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class MandiResponse(BaseResponse):
    """Schema for mandi response."""
    id: int
    name: str
    state: str
    district: str
    latitude: float
    longitude: float
    market_type: str
    pincode: Optional[str]
    contact_phone: Optional[str]
    is_active: bool
    created_at: datetime


class MandiListResponse(PaginatedResponse):
    """Schema for paginated mandi list."""
    items: List[MandiResponse]


class NearbyMandiRequest(BaseModel):
    """Schema for nearby mandi search."""
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    radius_km: int = Field(default=50, ge=1, le=500)
    limit: int = Field(default=10, ge=1, le=50)


class NearbyMandiResponse(BaseResponse):
    """Schema for nearby mandi with distance."""
    id: int
    name: str
    state: str
    district: str
    latitude: float
    longitude: float
    distance_km: float


# ==================== Price Schemas ====================

class PriceBase(BaseModel):
    """Base price schema."""
    mandi_id: int
    commodity_id: int
    price_date: date
    min_price: Optional[Decimal] = Field(default=None, ge=0)
    max_price: Optional[Decimal] = Field(default=None, ge=0)
    modal_price: Optional[Decimal] = Field(default=None, ge=0)
    arrival_qty: Optional[int] = Field(default=None, ge=0)


class PriceCreate(PriceBase):
    """Schema for creating a price record."""
    pass


class PriceResponse(BaseResponse):
    """Schema for price response."""
    id: int
    mandi_id: int
    commodity_id: int
    price_date: date
    min_price: Optional[float]
    max_price: Optional[float]
    modal_price: Optional[float]
    arrival_qty: Optional[int]
    created_at: datetime


class PriceWithDetailsResponse(BaseResponse):
    """Schema for price response with mandi and commodity details."""
    id: int
    mandi_id: int
    commodity_id: int
    price_date: date
    min_price: Optional[float]
    max_price: Optional[float]
    modal_price: Optional[float]
    arrival_qty: Optional[int]
    mandi: Optional[MandiResponse] = None
    commodity: Optional[CommodityResponse] = None
    created_at: datetime


class PriceListResponse(PaginatedResponse):
    """Schema for paginated price list."""
    items: List[PriceResponse]


class PriceHistoryRequest(BaseModel):
    """Schema for price history request."""
    commodity_id: int
    mandi_id: Optional[int] = None
    state: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: int = Field(default=30, ge=1, le=365)


class PriceHistoryResponse(BaseModel):
    """Schema for price history response."""
    commodity_id: int
    commodity_name: str
    mandi_id: Optional[int]
    mandi_name: Optional[str]
    prices: List[PriceResponse]


class PriceTrendPoint(BaseModel):
    """Schema for price trend data point."""
    date: date
    modal_price: float
    min_price: float
    max_price: float
    arrival_qty: Optional[int] = 0


# ==================== Alert Schemas ====================

class AlertBase(BaseModel):
    """Base alert schema."""
    commodity_id: int
    mandi_id: Optional[int] = None
    target_price: Decimal = Field(..., ge=0)
    condition: str = Field(default="above", pattern="^(above|below)$")
    notification_channels: str = Field(default="whatsapp")


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    target_price: Optional[Decimal] = Field(default=None, ge=0)
    condition: Optional[str] = Field(default=None, pattern="^(above|below)$")
    is_active: Optional[bool] = None
    notification_channels: Optional[str] = None


class AlertResponse(BaseResponse):
    """Schema for alert response."""
    id: int
    user_id: int
    commodity_id: int
    mandi_id: Optional[int]
    target_price: float
    condition: str
    is_active: bool
    is_triggered: bool
    triggered_at: Optional[datetime]
    notification_sent: bool
    notification_channels: str
    commodity: Optional[CommodityResponse] = None
    mandi: Optional[MandiResponse] = None
    created_at: datetime


class AlertListResponse(PaginatedResponse):
    """Schema for paginated alert list."""
    items: List[AlertResponse]


# ==================== Forecast Schemas ====================

class ForecastRequest(BaseModel):
    """Schema for forecast request."""
    commodity_id: int
    mandi_id: Optional[int] = None
    state: Optional[str] = None
    forecast_days: int = Field(default=7, ge=1, le=30)


class ForecastPoint(BaseModel):
    """Schema for a single forecast point."""
    date: date
    predicted_price: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: Optional[float] = None


class ForecastResponse(BaseModel):
    """Schema for forecast response."""
    commodity_id: int
    commodity_name: str
    mandi_id: Optional[int]
    mandi_name: Optional[str]
    forecast_date: datetime
    forecast_days: int
    current_price: Optional[float]
    predicted_change_percent: Optional[float]
    trend: str
    forecast: List[ForecastPoint]
    shap_explanation: Optional[dict] = None


# ==================== Routing Schemas ====================

class RoutingRequest(BaseModel):
    """Schema for routing request."""
    commodity_id: int
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    max_distance_km: int = Field(default=100, ge=1, le=500)
    quantity: Optional[float] = Field(default=None, ge=0)


class RoutingOption(BaseModel):
    """Schema for a routing option."""
    mandi: MandiResponse
    distance_km: float
    current_price: Optional[float]
    predicted_price: Optional[float]
    price_trend: Optional[str]
    estimated_profit: Optional[float]
    score: float
    recommendation: str


class RoutingResponse(BaseModel):
    """Schema for routing response."""
    commodity_id: int
    commodity_name: str
    user_location: dict
    best_options: List[RoutingOption]


# ==================== Voice Schemas ====================

class VoiceQueryRequest(BaseModel):
    """Schema for voice query request."""
    audio_base64: str
    language: str = Field(default="hi", max_length=10)


class VoiceQueryResponse(BaseModel):
    """Schema for voice query response."""
    transcript: str
    detected_language: str
    intent: Optional[str]
    entities: Optional[dict]
    response_text: str
    audio_base64: Optional[str] = None


# ==================== WhatsApp Schemas ====================

class WhatsAppWebhook(BaseModel):
    """Schema for WhatsApp webhook payload."""
    From: str
    Body: Optional[str] = None
    MediaUrl0: Optional[str] = None
    MediaContentType0: Optional[str] = None
    ProfileName: Optional[str] = None
    WaId: Optional[str] = None


class WhatsAppMessage(BaseModel):
    """Schema for sending WhatsApp message."""
    to: str
    body: str
    media_url: Optional[str] = None


# ==================== Health Check ====================

class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    timestamp: datetime
    database: str
    redis: str
