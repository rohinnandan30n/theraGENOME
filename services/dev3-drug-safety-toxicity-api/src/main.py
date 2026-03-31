from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from src.api.drugs import router as drugs_router
from src.db.connection import init_db, close_db
from src.cache.redis_cache import close_redis
from src.messaging.kafka_consumer import start_kafka_consumer, stop_kafka_consumer
from src.messaging.kafka_producer import close_kafka_producer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    print("🚀 Drug Safety & Toxicity API starting...")

    # Startup: Initialize databases
    try:
        print("📦 Initializing PostgreSQL...")
        await init_db()
        print("✅ PostgreSQL initialized")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")

    # Startup: Start Kafka consumer
    try:
        print("📨 Starting Kafka consumer...")
        await start_kafka_consumer()
        print("✅ Kafka consumer started")
    except Exception as e:
        logger.warning(f"Failed to start Kafka consumer (non-critical): {e}")

    yield

    # Shutdown: Clean up resources
    print("🛑 Shutting down...")
    try:
        await stop_kafka_consumer()
        await close_kafka_producer()
        await close_db()
        await close_redis()
        print("✅ All resources cleaned up")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="TheraGenome — Drug Safety & Toxicity API",
    version="0.1.0",
    description="Comprehensive drug safety, PGx, DDI, and adverse event API",
    lifespan=lifespan,
)

# Include API routers
app.include_router(drugs_router, prefix="/api/v1/drugs", tags=["Drugs"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "dev3-drug-safety-toxicity-api",
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """Root endpoint with documentation links."""
    return {
        "service": "TheraGenome Drug Safety & Toxicity API (Dev 3)",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "predict_toxicity": "POST /api/v1/drugs/predict-toxicity",
            "pgx": "GET /api/v1/drugs/pgx?gene=CYP2C9&drug=warfarin",
            "ddi": "POST /api/v1/drugs/ddi",
            "faers": "GET /api/v1/drugs/faers/{drug_name}",
            "health": "GET /health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
