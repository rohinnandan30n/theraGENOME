"""FastAPI application entry point for Pathogen & Resistance API."""

from fastapi import FastAPI
from src.api import pathogens_router
from src.db.connection import init_db

app = FastAPI(
    title="Pathogen & Resistance API",
    description="Microservice for bacterial genome ingestion and analysis",
    version="1.0.0",
)

# Initialize database
init_db()

# Include routers
app.include_router(pathogens_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
