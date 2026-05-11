"""
Rate limiting middleware and utilities using slowapi.

Implements per-IP rate limiting to prevent brute-force attacks and resource abuse.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Create rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_limiter() -> Limiter:
    """Get the global rate limiter instance."""
    return limiter


def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom error handler for rate limit exceeded.
    
    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception
        
    Returns:
        JSON response with 429 status code
    """
    client_ip = request.client.host if request.client else "unknown"
    
    logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Setup rate limiting for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add custom exception handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
    
    logger.info("Rate limiting configured")


# Rate limit definitions
RATE_LIMITS = {
    "auth_token": "5/minute",          # 5 requests per minute for /auth/token
    "auth_refresh": "10/minute",       # 10 requests per minute for /auth/refresh-token
    "api_default": "100/minute",       # 100 requests per minute for general API
    "public_endpoint": "1000/hour",    # 1000 requests per hour for public endpoints
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit for endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (auth_token, api_default, etc.)
        
    Returns:
        Rate limit string for slowapi
    """
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["api_default"])
