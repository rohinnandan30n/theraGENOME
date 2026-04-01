from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from src.api.ingestion import router as ingestion_router
from src.api.variants import router as variants_router
from src.api.classification import router as classification_router
from src.db.connection import db
from src.config import APP_HOST, APP_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    try:
        logger.info("Initializing database schema...")
        db.init_db()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


# Create FastAPI app
app = FastAPI(
    title="theraGENOME - Genomics & Variant API",
    description="API for genomic data ingestion and variant interpretation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion_router)
app.include_router(variants_router)
app.include_router(classification_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "theraGENOME Genomics API"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "title": "theraGENOME - Genomics & Variant API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "ingestion": "/api/v1/ingestion",
            "variants": "/api/v1/variants",
            "classification": "/api/v1/classification"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {APP_HOST}:{APP_PORT}")
    uvicorn.run(
        app,
        host=APP_HOST,
        port=APP_PORT,
        log_level="info"
    )
