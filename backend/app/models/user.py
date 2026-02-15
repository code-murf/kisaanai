"""
User model for authentication and user management.
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Boolean, TIMESTAMP, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.alert import Alert


class User(Base):
    """Model for user accounts."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    whatsapp_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
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
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_users_phone", "phone_number"),
        Index("idx_users_whatsapp", "whatsapp_id"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone='{self.phone_number}', name='{self.full_name}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "email": self.email,
            "full_name": self.full_name,
            "preferred_language": self.preferred_language,
            "state": self.state,
            "district": self.district,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "whatsapp_id": self.whatsapp_id,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OTPVerification(Base):
    """Model for OTP verification codes."""
    
    __tablename__ = "otp_verifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), default="login")
    is_used: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_otp_phone_purpose", "phone_number", "purpose"),
    )
    
    def __repr__(self) -> str:
        return f"<OTPVerification(id={self.id}, phone='{self.phone_number}', purpose='{self.purpose}')>"
    
    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def is_valid(self) -> bool:
        """Check if OTP is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "purpose": self.purpose,
            "is_used": self.is_used,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RefreshToken(Base):
    """Model for refresh tokens."""
    
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not revoked and not expired)."""
        return not self.revoked and not self.is_expired()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
