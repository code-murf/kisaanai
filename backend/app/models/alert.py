"""
Alert model for price alerts.
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, Numeric, TIMESTAMP, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.commodity import Commodity
    from app.models.mandi import Mandi


class Alert(Base):
    """Model for price alerts."""
    
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    commodity_id: Mapped[int] = mapped_column(
        ForeignKey("commodities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mandi_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("mandis.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), default="above")
    is_active: Mapped[bool] = mapped_column(default=True)
    is_triggered: Mapped[bool] = mapped_column(default=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notification_sent: Mapped[bool] = mapped_column(default=False)
    notification_channels: Mapped[Optional[str]] = mapped_column(String(100), default="whatsapp")
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
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="alerts")
    mandi: Mapped[Optional["Mandi"]] = relationship("Mandi", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index("idx_alerts_user_active", "user_id", "is_active"),
        Index("idx_alerts_commodity_mandi", "commodity_id", "mandi_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, user_id={self.user_id}, commodity_id={self.commodity_id}, target={self.target_price})>"
    
    def should_trigger(self, current_price: Decimal) -> bool:
        """Check if alert should trigger based on current price."""
        if self.condition == "above":
            return current_price >= self.target_price
        elif self.condition == "below":
            return current_price <= self.target_price
        return False
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "commodity_id": self.commodity_id,
            "mandi_id": self.mandi_id,
            "target_price": float(self.target_price) if self.target_price else None,
            "condition": self.condition,
            "is_active": self.is_active,
            "is_triggered": self.is_triggered,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "notification_sent": self.notification_sent,
            "notification_channels": self.notification_channels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
