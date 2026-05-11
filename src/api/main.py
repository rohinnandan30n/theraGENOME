"""
Main FastAPI application for theraGENOME API

Sets up the server, configures middleware, and registers routes.
Includes security hardening: rate limiting, input validation, security headers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Import routes
from .routes.therapist_routes import router as therapist_router
from .routes.auth_routes import router as auth_router
from .routes import variant_routes, pathogen_routes, drug_routes, report_routes

# Import security utilities
from .security_utils import SecurityHeadersMiddleware, log_security_event
from .rate_limiting import setup_rate_limiting, get_limiter, get_rate_limit

# Import classification for model status
from .classification import get_classifier

# Configure logging
def setup_logging():
    """Configure application logging."""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    # Startup
    logger.info("=== theraGENOME API Starting ===")
    logger.info(f"Server started at {datetime.utcnow().isoformat()}")
    
    yield
    
    # Shutdown
    logger.info("=== theraGENOME API Shutting Down ===")
    logger.info(f"Server stopped at {datetime.utcnow().isoformat()}")


# Create FastAPI application
app = FastAPI(
    title="theraGENOME API",
    description="Healthcare application for therapy management and genomic data integration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com", "testserver"]
)

# Add security headers middleware (must be added after other middleware)
app.add_middleware(SecurityHeadersMiddleware)

# Setup rate limiting
setup_rate_limiting(app)

logger.info("Security middleware configured: CORS, Trusted Hosts, Security Headers, Rate Limiting")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error for {request.url.path}: {exc}")
    
    # Sanitize errors to remove non-serializable objects
    errors = []
    for error in exc.errors():
        sanitized_error = {
            'type': error.get('type'),
            'loc': error.get('loc'),
            'msg': error.get('msg'),
        }
        errors.append(sanitized_error)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": errors
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status of the application including model status
    """
    try:
        classifier = get_classifier()
        model_status = classifier.ensemble_classifier.get_model_status()
    except Exception as e:
        logger.warning(f"Could not retrieve model status: {e}")
        model_status = {"error": "Could not retrieve model status"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "theraGENOME API",
        "model_status": model_status
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API metadata and available endpoints
    """
    return {
        "service": "theraGENOME API",
        "version": "1.0.0",
        "description": "Healthcare application for therapy management and genomic data integration",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/health",
            "therapists": "/api/v1/therapists"
        }
    }


# Include routers
app.include_router(auth_router)
app.include_router(therapist_router)
app.include_router(variant_routes.router)
app.include_router(pathogen_routes.router)
app.include_router(drug_routes.router)
app.include_router(report_routes.router)

logger.info("FastAPI application configured successfully")


# For development/testing
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
