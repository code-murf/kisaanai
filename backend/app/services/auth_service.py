"""
Authentication Service for user registration, login, and token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, OTPVerification, RefreshToken
from app.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
    LoginRequest,
    OTPRequest,
    OTPVerifyRequest,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_otp,
)


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get a user by phone number."""
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def register_user(
        self,
        user_data: UserCreate,
    ) -> Tuple[User, TokenResponse]:
        """
        Register a new user.
        
        Returns the created user and initial tokens.
        """
        # Check if phone number already exists
        existing_user = await self.get_user_by_phone(user_data.phone_number)
        if existing_user:
            raise ValueError("Phone number already registered")
        
        # Check email if provided
        if user_data.email:
            existing_email = await self.get_user_by_email(user_data.email)
            if existing_email:
                raise ValueError("Email already registered")
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            phone_number=user_data.phone_number,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            state=user_data.state,
            district=user_data.district,
            preferred_language=user_data.preferred_language or "en",
        )
        
        self.db.add(user)
        await self.db.flush()
        
        # Generate tokens
        access_token = create_access_token(
            subject=user.id,
            additional_claims={"phone": user.phone_number}
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(refresh_token_record)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes in seconds
        )
        
        return user, tokens
    
    async def login_password(
        self,
        login_data: LoginRequest,
    ) -> Tuple[User, TokenResponse]:
        """
        Authenticate user with phone number and password.
        
        Returns user and tokens on success.
        """
        user = await self.get_user_by_phone(login_data.phone_number)
        
        if not user:
            raise ValueError("Invalid phone number or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        if not user.hashed_password:
            raise ValueError("Password not set for this account. Use OTP login.")
        
        if not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid phone number or password")
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Generate tokens
        access_token = create_access_token(
            subject=user.id,
            additional_claims={"phone": user.phone_number}
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        # Store refresh token
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(refresh_token_record)
        
        await self.db.commit()
        
        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60,
        )
        
        return user, tokens
    
    async def request_otp(
        self,
        otp_data: OTPRequest,
    ) -> str:
        """
        Request OTP for phone number verification.
        
        Returns the OTP (in production, this would be sent via SMS).
        """
        # Check if user exists
        user = await self.get_user_by_phone(otp_data.phone_number)
        
        # Generate OTP
        otp_code = generate_otp(length=6)
        
        # Invalidate any existing OTPs for this phone
        await self.db.execute(
            select(OTPVerification).where(
                and_(
                    OTPVerification.phone_number == otp_data.phone_number,
                    OTPVerification.is_used == False,
                )
            )
        )
        # Mark existing OTPs as used
        existing_otps = await self.db.execute(
            select(OTPVerification).where(
                and_(
                    OTPVerification.phone_number == otp_data.phone_number,
                    OTPVerification.is_used == False,
                )
            )
        )
        for existing_otp in existing_otps.scalars().all():
            existing_otp.is_used = True
        
        # Create new OTP record
        otp_record = OTPVerification(
            phone_number=otp_data.phone_number,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            purpose=otp_data.purpose,
        )
        self.db.add(otp_record)
        
        await self.db.commit()
        
        # In production, send OTP via SMS
        # await send_sms(otp_data.phone_number, f"Your OTP is {otp_code}")
        
        return otp_code
    
    async def verify_otp(
        self,
        verify_data: OTPVerifyRequest,
    ) -> Tuple[Optional[User], TokenResponse]:
        """
        Verify OTP and authenticate user.
        
        For login purpose: Returns user and tokens if verified.
        For registration: Returns None if user doesn't exist.
        """
        # Find valid OTP
        result = await self.db.execute(
            select(OTPVerification).where(
                and_(
                    OTPVerification.phone_number == verify_data.phone_number,
                    OTPVerification.otp_code == verify_data.otp_code,
                    OTPVerification.is_used == False,
                    OTPVerification.expires_at > datetime.utcnow(),
                )
            )
        )
        otp_record = result.scalar_one_or_none()
        
        if not otp_record:
            raise ValueError("Invalid or expired OTP")
        
        # Mark OTP as used
        otp_record.is_used = True
        otp_record.verified_at = datetime.utcnow()
        
        # Check if user exists
        user = await self.get_user_by_phone(verify_data.phone_number)
        
        if verify_data.purpose == "login":
            if not user:
                raise ValueError("Account not found. Please register first.")
            
            if not user.is_active:
                raise ValueError("Account is disabled")
            
            # Update last login
            user.last_login = datetime.utcnow()
        
        await self.db.flush()
        
        if user:
            # Generate tokens
            access_token = create_access_token(
                subject=user.id,
                additional_claims={"phone": user.phone_number}
            )
            refresh_token = create_refresh_token(subject=user.id)
            
            # Store refresh token
            refresh_token_record = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            self.db.add(refresh_token_record)
            
            await self.db.commit()
            
            tokens = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=30 * 60,
            )
            
            return user, tokens
        else:
            await self.db.commit()
            return None, None
    
    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Returns new access and refresh tokens.
        """
        # Verify the token
        user_id = verify_token(refresh_token, "refresh")
        if not user_id:
            raise ValueError("Invalid refresh token")
        
        # Check if token exists in database
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token == refresh_token,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow(),
                )
            )
        )
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            raise ValueError("Invalid or expired refresh token")
        
        # Get user
        user = await self.get_user_by_id(int(user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or disabled")
        
        # Revoke old refresh token
        token_record.is_revoked = True
        
        # Generate new tokens
        access_token = create_access_token(
            subject=user.id,
            additional_claims={"phone": user.phone_number}
        )
        new_refresh_token = create_refresh_token(subject=user.id)
        
        # Store new refresh token
        new_token_record = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(new_token_record)
        
        await self.db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=30 * 60,
        )
    
    async def logout(self, user_id: int, refresh_token: Optional[str] = None) -> bool:
        """
        Logout user by revoking refresh tokens.
        
        If refresh_token is provided, revoke only that token.
        Otherwise, revoke all tokens for the user.
        """
        if refresh_token:
            result = await self.db.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.token == refresh_token,
                        RefreshToken.user_id == user_id,
                    )
                )
            )
            token_record = result.scalar_one_or_none()
            if token_record:
                token_record.is_revoked = True
        else:
            # Revoke all tokens for user
            result = await self.db.execute(
                select(RefreshToken).where(
                    and_(
                        RefreshToken.user_id == user_id,
                        RefreshToken.is_revoked == False,
                    )
                )
            )
            for token in result.scalars().all():
                token.is_revoked = True
        
        await self.db.commit()
        return True
    
    async def update_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> Optional[User]:
        """Update user profile."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        if full_name is not None:
            user.full_name = full_name
        if email is not None:
            # Check if email is already used
            existing = await self.get_user_by_email(email)
            if existing and existing.id != user_id:
                raise ValueError("Email already in use")
            user.email = email
        if state is not None:
            user.state = state
        if district is not None:
            user.district = district
        if preferred_language is not None:
            user.preferred_language = preferred_language
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        # Revoke all refresh tokens (force re-login)
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                )
            )
        )
        for token in result.scalars().all():
            token.is_revoked = True
        
        await self.db.commit()
        return True
    
    async def reset_password_request(self, phone_number: str) -> str:
        """
        Request password reset via OTP.
        
        Returns OTP code.
        """
        user = await self.get_user_by_phone(phone_number)
        if not user:
            raise ValueError("Account not found")
        
        # Generate and send OTP
        otp_data = OTPRequest(phone_number=phone_number, purpose="reset")
        return await self.request_otp(otp_data)
    
    async def reset_password(
        self,
        phone_number: str,
        otp_code: str,
        new_password: str,
    ) -> bool:
        """Reset password using OTP verification."""
        # Verify OTP
        verify_data = OTPVerifyRequest(
            phone_number=phone_number,
            otp_code=otp_code,
            purpose="reset",
        )
        
        user, _ = await self.verify_otp(verify_data)
        if not user:
            raise ValueError("OTP verification failed")
        
        # Set new password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    async def delete_account(self, user_id: int) -> bool:
        """Soft delete user account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Revoke all tokens
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                )
            )
        )
        for token in result.scalars().all():
            token.is_revoked = True
        
        await self.db.commit()
        return True
    
    @staticmethod
    def to_response(user: User) -> UserResponse:
        """Convert User model to response schema."""
        return UserResponse.model_validate(user)
