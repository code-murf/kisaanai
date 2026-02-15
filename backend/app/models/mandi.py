"""
Mandi model for agricultural markets with geospatial data.
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, TIMESTAMP, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.price import Price
    from app.models.weather import Weather
    from app.models.alert import Alert


class Mandi(Base):
    """Model for agricultural markets (Mandis) with geospatial data."""
    
    __tablename__ = "mandis"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[Decimal] = mapped_column(nullable=False)
    longitude: Mapped[Decimal] = mapped_column(nullable=False)
    # location: Mapped[Optional[str]] = mapped_column(
    #     Geography(geometry_type="POINT", srid=4326),
    #     nullable=True
    # )
    market_type: Mapped[str] = mapped_column(String(50), default="Regulated")
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    prices: Mapped[List["Price"]] = relationship(
        "Price",
        back_populates="mandi",
        cascade="all, delete-orphan"
    )
    weather: Mapped[List["Weather"]] = relationship(
        "Weather",
        back_populates="mandi",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="mandi",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_mandis_state_district", "state", "district"),
        # Index("idx_mandis_location", "location", postgresql_using="gist"),
    )
    
    def __repr__(self) -> str:
        return f"<Mandi(id={self.id}, name='{self.name}', state='{self.state}', district='{self.district}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "district": self.district,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "market_type": self.market_type,
            "pincode": self.pincode,
            "contact_phone": self.contact_phone,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in kilometers.
        """
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
