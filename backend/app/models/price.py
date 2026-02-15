"""
Price model for commodity prices at mandis.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Integer, Numeric, String, TIMESTAMP, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.commodity import Commodity
    from app.models.mandi import Mandi


class Price(Base):
    """Model for commodity prices at mandis."""
    
    __tablename__ = "prices"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mandi_id: Mapped[int] = mapped_column(
        ForeignKey("mandis.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    commodity_id: Mapped[int] = mapped_column(
        ForeignKey("commodities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    price_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    min_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    max_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    modal_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    arrival_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    mandi: Mapped["Mandi"] = relationship("Mandi", back_populates="prices")
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="prices")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("mandi_id", "commodity_id", "price_date", name="uq_price_mandi_commodity_date"),
        Index("idx_prices_date", "price_date"),
        Index("idx_prices_mandi_commodity", "mandi_id", "commodity_id"),
        Index("idx_prices_commodity_date", "commodity_id", "price_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Price(id={self.id}, mandi_id={self.mandi_id}, commodity_id={self.commodity_id}, date={self.price_date})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "mandi_id": self.mandi_id,
            "commodity_id": self.commodity_id,
            "price_date": self.price_date.isoformat() if self.price_date else None,
            "min_price": float(self.min_price) if self.min_price else None,
            "max_price": float(self.max_price) if self.max_price else None,
            "modal_price": float(self.modal_price) if self.modal_price else None,
            "arrival_qty": self.arrival_qty,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
