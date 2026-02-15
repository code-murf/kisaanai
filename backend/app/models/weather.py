"""
Weather model for weather observations at mandis.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, String, Integer, Numeric, TIMESTAMP, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.mandi import Mandi


class Weather(Base):
    """Model for weather observations at mandis."""
    
    __tablename__ = "weather"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mandi_id: Mapped[int] = mapped_column(
        ForeignKey("mandis.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    observation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    temperature_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    temperature_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    humidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rainfall_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    wind_speed_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    weather_condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
    mandi: Mapped["Mandi"] = relationship("Mandi", back_populates="weather")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("mandi_id", "observation_date", name="uq_weather_mandi_date"),
        Index("idx_weather_date", "observation_date"),
        Index("idx_weather_mandi_date", "mandi_id", "observation_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Weather(id={self.id}, mandi_id={self.mandi_id}, date={self.observation_date})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "mandi_id": self.mandi_id,
            "observation_date": self.observation_date.isoformat() if self.observation_date else None,
            "temperature_max": float(self.temperature_max) if self.temperature_max else None,
            "temperature_min": float(self.temperature_min) if self.temperature_min else None,
            "humidity": self.humidity,
            "rainfall_mm": float(self.rainfall_mm) if self.rainfall_mm else None,
            "wind_speed_kmh": float(self.wind_speed_kmh) if self.wind_speed_kmh else None,
            "weather_condition": self.weather_condition,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
