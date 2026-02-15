"""
Authentication API endpoints.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
    LoginRequest,
    OTPRequest,
    OTPVerifyRequest,
    SuccessResponse,
    ErrorDetail,
)
from app.core.security import verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    return AuthService.to_response(user)


async def get_current_user_id(
    current_user: UserResponse = Depends(get_current_user),
) -> int:
    """Dependency to get just the current user ID."""
    return current_user.id


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with phone number and password.",
    responses={
        201: {"description": "User registered successfully"},
        400: {"model": ErrorDetail, "description": "Phone number or email already registered"},
    },
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    auth_service = AuthService(db)
    
    try:
        user, tokens = await auth_service.register_user(user_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with phone and password",
    description="Authenticate user with phone number and password.",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorDetail, "description": "Invalid credentials"},
    },
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with phone number and password."""
    auth_service = AuthService(db)
    
    try:
        user, tokens = await auth_service.login_password(login_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/otp/request",
    response_model=SuccessResponse,
    summary="Request OTP",
    description="Request an OTP for phone verification. OTP will be sent via SMS.",
    responses={
        200: {"description": "OTP sent successfully"},
        429: {"model": ErrorDetail, "description": "Too many requests"},
    },
)
async def request_otp(
    otp_data: OTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request OTP for phone verification."""
    auth_service = AuthService(db)
    
    try:
        otp_code = await auth_service.request_otp(otp_data)
        
        # In development, return the OTP code
        # In production, this would be sent via SMS and not returned
        message = "OTP sent successfully"
        if request.app.state.debug:
            message = f"OTP sent successfully. Code: {otp_code}"
        
        return SuccessResponse(message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/otp/verify",
    response_model=TokenResponse,
    summary="Verify OTP and login",
    description="Verify OTP code and authenticate user. For login, user must already exist.",
    responses={
        200: {"description": "OTP verified, login successful"},
        400: {"model": ErrorDetail, "description": "Invalid or expired OTP"},
    },
)
async def verify_otp(
    verify_data: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and authenticate."""
    auth_service = AuthService(db)
    
    try:
        user, tokens = await auth_service.verify_otp(verify_data)
        
        if not user or not tokens:
            # OTP verified but user doesn't exist (for registration flow)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found. Please register first.",
            )
        
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access and refresh tokens using a valid refresh token.",
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"model": ErrorDetail, "description": "Invalid refresh token"},
    },
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    auth_service = AuthService(db)
    
    try:
        tokens = await auth_service.refresh_tokens(refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout user",
    description="Revoke refresh tokens to logout user.",
)
async def logout(
    refresh_token: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Logout user by revoking refresh tokens."""
    auth_service = AuthService(db)
    await auth_service.logout(current_user_id, refresh_token)
    return SuccessResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
)
async def get_me(
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile",
    description="Update the current user's profile information.",
)
async def update_profile(
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    preferred_language: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.update_profile(
            user_id=current_user_id,
            full_name=full_name,
            email=email,
            state=state,
            district=district,
            preferred_language=preferred_language,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return AuthService.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change password",
    description="Change the current user's password. This will revoke all active sessions.",
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    auth_service = AuthService(db)
    
    try:
        await auth_service.change_password(
            user_id=current_user_id,
            current_password=current_password,
            new_password=new_password,
        )
        return SuccessResponse(message="Password changed successfully. Please login again.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/reset-password/request",
    response_model=SuccessResponse,
    summary="Request password reset",
    description="Request OTP for password reset.",
)
async def reset_password_request(
    phone_number: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset OTP."""
    auth_service = AuthService(db)
    
    try:
        otp_code = await auth_service.reset_password_request(phone_number)
        
        message = "Reset OTP sent successfully"
        if request.app.state.debug:
            message = f"Reset OTP sent successfully. Code: {otp_code}"
        
        return SuccessResponse(message=message)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/reset-password",
    response_model=SuccessResponse,
    summary="Reset password",
    description="Reset password using OTP verification.",
)
async def reset_password(
    phone_number: str,
    otp_code: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
):
    """Reset password with OTP."""
    auth_service = AuthService(db)
    
    try:
        await auth_service.reset_password(
            phone_number=phone_number,
            otp_code=otp_code,
            new_password=new_password,
        )
        return SuccessResponse(message="Password reset successfully. Please login.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/me",
    response_model=SuccessResponse,
    summary="Delete account",
    description="Soft delete the current user's account.",
)
async def delete_account(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete user account (soft delete)."""
    auth_service = AuthService(db)
    
    success = await auth_service.delete_account(current_user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return SuccessResponse(message="Account deleted successfully")
