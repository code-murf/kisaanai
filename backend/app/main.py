"""
Main FastAPI application for the Agri-Analytics platform.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.api import auth, commodities, mandis, prices, forecasts, routing, webhooks, weather, crops, diseases, voice, voice_agent, community, resource
from app.schemas import ErrorDetail

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    app.state.debug = settings.DEBUG
    print(f"Starting {settings.APP_NAME}...")
    print(f"Debug mode: {settings.DEBUG}")
    
    # Initialize AI service shared session for connection pooling
    try:
        from app.services.ai_service import GroqAIService
        await GroqAIService.get_shared_session()
        logger.info("Initialized AI service shared session with connection pooling")
    except Exception as e:
        logger.warning(f"Could not initialize AI service session: {e}")
    
    # Initialize voice session manager
    try:
        from app.core.voice_session import get_session_manager
        manager = get_session_manager()
        logger.info(f"Initialized voice session manager (timeout={manager._session_timeout}s)")
    except Exception as e:
        logger.warning(f"Could not initialize voice session manager: {e}")
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")
    
    # Close AI service shared session
    try:
        from app.services.ai_service import GroqAIService
        await GroqAIService.close_session()
        logger.info("Closed AI service shared session")
    except Exception as e:
        logger.warning(f"Error closing AI service session: {e}")
    
    # Clean up voice sessions
    try:
        from app.core.voice_session import reset_session_manager
        reset_session_manager()
        logger.info("Cleaned up voice session manager")
    except Exception as e:
        logger.warning(f"Error cleaning up voice session manager: {e}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
# Agri-Analytics Platform API

A comprehensive platform for agricultural commodity price analytics, forecasting, and market intelligence.

## Features

- **Price Tracking**: Real-time and historical commodity prices across Indian mandis
- **Price Forecasting**: ML-powered price predictions using XGBoost
- **Market Routing**: Optimal mandi recommendations based on price and distance
- **Voice Support**: Multilingual voice queries via Bhashini ASR/TTS
- **WhatsApp Bot**: Easy access via WhatsApp messaging

## Authentication

Most endpoints require authentication using JWT tokens. Obtain a token via the `/auth/login` or `/auth/otp/verify` endpoints.

Include the token in the Authorization header: `Bearer <token>`
        """,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(commodities.router, prefix="/api/v1")
    app.include_router(mandis.router, prefix="/api/v1")
    app.include_router(prices.router, prefix="/api/v1")
    app.include_router(forecasts.router, prefix="/api/v1")
    app.include_router(routing.router, prefix="/api/v1")
    app.include_router(weather.router, prefix="/api/v1")
    app.include_router(crops.router, prefix="/api/v1")
    app.include_router(diseases.router, prefix="/api/v1")
    # Voice router already uses prefix="/voice". Mount it under /api/v1 and
    # also keep legacy direct /voice paths for backward compatibility.
    app.include_router(voice.router, prefix="/api/v1", tags=["Voice"])
    app.include_router(voice.router, tags=["Voice"])
    app.include_router(voice_agent.router, prefix="/api/v1/voice", tags=["Voice Agent"])
    app.include_router(community.router, prefix="/api/v1")
    app.include_router(resource.router, prefix="/api/v1")
    app.include_router(webhooks.router)  # Webhooks at /webhooks (no version prefix for external services)
    
    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle validation errors with detailed messages."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected errors."""
        if settings.DEBUG:
            import traceback
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.PROJECT_NAME,
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
            "health": "/health",
        }
    
    return app


# Create the application instance
app = create_application()
