"""
Federated Learning Admin Service
Manages FL rounds, triggers training, and handles metrics logging
Port: 8004
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import httpx

# Import FL-related modules
from fl_schemas import FLRoundCreate, FLRoundResponse, FLClientMetrics, FLAggregatedMetrics
from fl_repository import FLRoundRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
FLOWER_SERVER_URL = os.getenv("FLOWER_SERVER_URL", "http://localhost:8080")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/theragenome")
MIN_CLIENTS_PER_ROUND = int(os.getenv("MIN_CLIENTS_PER_ROUND", "3"))
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "10"))
ROUND_TIMEOUT_SECONDS = int(os.getenv("ROUND_TIMEOUT_SECONDS", "300"))

# Database setup
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Repository instance (lazy loaded)
fl_repository: Optional[FLRoundRepository] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class StartRoundRequest(BaseModel):
    """Request to start a new FL round"""
    round_number: Optional[int] = Field(None, description="Explicit round number, auto-increment if omitted")
    max_clients: int = Field(10, ge=MIN_CLIENTS_PER_ROUND, le=1000, description="Max clients to participate")
    timeout_seconds: int = Field(ROUND_TIMEOUT_SECONDS, ge=10, le=3600, description="Round timeout")
    description: Optional[str] = Field(None, description="Round description/notes")


class StartRoundResponse(BaseModel):
    """Response from starting a round"""
    round_id: str
    round_number: int
    status: str = "initiated"
    max_clients: int
    timeout_seconds: int
    started_at: str
    message: str


class RoundStatusResponse(BaseModel):
    """Current status of a round"""
    round_id: str
    round_number: int
    status: str  # initiated, running, aggregating, completed, failed
    num_clients: Optional[int] = None
    client_metrics: Optional[List[FLClientMetrics]] = None
    aggregated_metrics: Optional[FLAggregatedMetrics] = None
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class RoundHistoryResponse(BaseModel):
    """Historical round data"""
    round_number: int
    num_clients: int
    aggregated_loss: float
    aggregated_accuracy: float
    timestamp: str
    duration_seconds: float


class SystemStatusResponse(BaseModel):
    """Overall system status"""
    service: str = "FL Admin Service"
    version: str = "1.0.0"
    status: str  # healthy, degraded, error
    flower_server_status: str
    database_status: str
    current_round: Optional[int] = None
    total_rounds_completed: int = 0
    min_clients_required: int = MIN_CLIENTS_PER_ROUND
    max_rounds: int = MAX_ROUNDS
    message: str


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle - startup and shutdown"""
    global fl_repository
    
    logger.info("🚀 FL Admin Service starting...")
    
    try:
        # Initialize repository
        fl_repository = FLRoundRepository(AsyncSessionLocal)
        
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        
        # Test Flower server connection
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{FLOWER_SERVER_URL}/status")
                logger.info(f"✅ Flower server online: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️  Flower server may be offline: {e}")
        
        logger.info("✅ FL Admin Service ready")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    finally:
        logger.info("🛑 FL Admin Service shutting down...")
        await engine.dispose()


# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="FL Admin Service",
    description="Federated Learning Orchestration & Metrics",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Business Logic Functions
# ============================================================================

async def trigger_flower_round(
    round_number: int,
    max_clients: int,
    timeout_seconds: int
) -> Dict[str, Any]:
    """
    Trigger a training round on Flower server
    
    Returns:
        {
            "success": bool,
            "round_id": str,
            "message": str,
            "data": {...}
        }
    """
    try:
        payload = {
            "round_number": round_number,
            "max_clients": max_clients,
            "timeout_seconds": timeout_seconds,
        }
        
        timeout = httpx.Timeout(timeout_seconds + 30)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{FLOWER_SERVER_URL}/rounds/start",
                json=payload
            )
            
            if response.status_code not in [200, 202]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Flower server error: {response.text}"
                )
            
            return response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Flower server timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot reach Flower server")
    except Exception as e:
        logger.error(f"Error triggering Flower round: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def log_round_metrics(
    round_number: int,
    num_clients: int,
    aggregated_loss: float,
    aggregated_accuracy: float
) -> dict:
    """Log round metrics to database"""
    if not fl_repository:
        raise RuntimeError("FL Repository not initialized")
    
    round_data = FLRoundCreate(
        round_number=round_number,
        num_clients=num_clients,
        aggregated_loss=aggregated_loss,
        aggregated_accuracy=aggregated_accuracy,
        status="completed"
    )
    
    async with AsyncSessionLocal() as session:
        return await fl_repository.create_round(session, round_data)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Simple health check"""
    return {
        "status": "healthy",
        "service": "FL Admin Service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status", response_model=SystemStatusResponse, tags=["Status"])
async def system_status() -> SystemStatusResponse:
    """Get overall system status"""
    
    # Check Flower server
    flower_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{FLOWER_SERVER_URL}/status")
            flower_status = "online" if response.status_code == 200 else "error"
    except:
        flower_status = "offline"
    
    # Check database
    db_status = "error"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            db_status = "online"
    except:
        pass
    
    # Get statistics
    total_rounds = 0
    current_round = None
    if fl_repository:
        try:
            async with AsyncSessionLocal() as session:
                rounds = await fl_repository.get_all_rounds(session)
                if rounds:
                    total_rounds = len(rounds)
                    current_round = rounds[-1].round_number
        except Exception as e:
            logger.warning(f"Could not fetch round stats: {e}")
    
    overall_status = "healthy" if (flower_status == "online" and db_status == "online") else "degraded"
    
    return SystemStatusResponse(
        status=overall_status,
        flower_server_status=flower_status,
        database_status=db_status,
        current_round=current_round,
        total_rounds_completed=total_rounds,
        message=f"System {overall_status}: Flower {flower_status}, DB {db_status}"
    )


# ============================================================================
# FL Round Endpoints
# ============================================================================

@app.post("/fl/start-round", response_model=StartRoundResponse, tags=["FL Operations"])
async def start_fl_round(
    request: StartRoundRequest,
    background_tasks: BackgroundTasks
) -> StartRoundResponse:
    """
    Trigger a new federated learning round
    
    - Calls Flower server to start aggregation
    - Enforces minimum clients (3)
    - Returns round_id for tracking
    - Logs metrics asynchronously
    """
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        # Get next round number
        round_number = request.round_number
        if round_number is None:
            async with AsyncSessionLocal() as session:
                last_round = await fl_repository.get_last_round(session)
                round_number = (last_round.round_number + 1) if last_round else 1
        
        # Check if we've exceeded max rounds
        if round_number > MAX_ROUNDS:
            raise HTTPException(
                status_code=400,
                detail=f"Max rounds ({MAX_ROUNDS}) exceeded"
            )
        
        logger.info(f"🟢 Starting FL Round {round_number}...")
        
        # Trigger Flower round
        flower_response = await trigger_flower_round(
            round_number=round_number,
            max_clients=request.max_clients,
            timeout_seconds=request.timeout_seconds
        )
        
        round_id = flower_response.get("round_id", f"round_{round_number}_{datetime.utcnow().timestamp()}")
        
        # Log to database
        round_data = FLRoundCreate(
            round_number=round_number,
            num_clients=0,  # Will be updated when round completes
            aggregated_loss=None,
            aggregated_accuracy=None,
            status="initiated"
        )
        
        async with AsyncSessionLocal() as session:
            db_round = await fl_repository.create_round(session, round_data)
        
        logger.info(f"✅ Round {round_number} initiated with ID: {round_id}")
        
        return StartRoundResponse(
            round_id=round_id,
            round_number=round_number,
            status="initiated",
            max_clients=request.max_clients,
            timeout_seconds=request.timeout_seconds,
            started_at=datetime.utcnow().isoformat(),
            message=f"Round {round_number} triggered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting round: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fl/rounds/latest", response_model=RoundStatusResponse, tags=["FL Operations"])
async def get_latest_round() -> RoundStatusResponse:
    """Get status of the latest FL round"""
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            last_round = await fl_repository.get_last_round(session)
            
            if not last_round:
                raise HTTPException(status_code=404, detail="No rounds found")
            
            return RoundStatusResponse(
                round_id=f"round_{last_round.round_number}",
                round_number=last_round.round_number,
                status=last_round.status,
                num_clients=last_round.num_clients,
                aggregated_metrics=FLAggregatedMetrics(
                    aggregated_loss=last_round.aggregated_loss,
                    aggregated_accuracy=last_round.aggregated_accuracy
                ) if last_round.aggregated_loss is not None else None,
                started_at=last_round.created_at.isoformat(),
                completed_at=last_round.updated_at.isoformat() if last_round.updated_at else None,
                error=last_round.error_message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest round: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fl/rounds/{round_number}", response_model=RoundStatusResponse, tags=["FL Operations"])
async def get_round_status(round_number: int) -> RoundStatusResponse:
    """Get status of a specific FL round"""
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            round_data = await fl_repository.get_round_by_number(session, round_number)
            
            if not round_data:
                raise HTTPException(status_code=404, detail=f"Round {round_number} not found")
            
            return RoundStatusResponse(
                round_id=f"round_{round_data.round_number}",
                round_number=round_data.round_number,
                status=round_data.status,
                num_clients=round_data.num_clients,
                aggregated_metrics=FLAggregatedMetrics(
                    aggregated_loss=round_data.aggregated_loss,
                    aggregated_accuracy=round_data.aggregated_accuracy
                ) if round_data.aggregated_loss is not None else None,
                started_at=round_data.created_at.isoformat(),
                completed_at=round_data.updated_at.isoformat() if round_data.updated_at else None,
                error=round_data.error_message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching round {round_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fl/rounds/history/summary", response_model=List[RoundHistoryResponse], tags=["FL Operations"])
async def get_rounds_history() -> List[RoundHistoryResponse]:
    """Get historical summary of all rounds"""
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            rounds = await fl_repository.get_all_rounds(session)
            
            history = []
            for r in rounds:
                if r.aggregated_loss is not None:
                    duration = (r.updated_at - r.created_at).total_seconds() if r.updated_at else 0
                    history.append(
                        RoundHistoryResponse(
                            round_number=r.round_number,
                            num_clients=r.num_clients or 0,
                            aggregated_loss=r.aggregated_loss,
                            aggregated_accuracy=r.aggregated_accuracy or 0.0,
                            timestamp=r.created_at.isoformat(),
                            duration_seconds=duration
                        )
                    )
            
            return history
            
    except Exception as e:
        logger.error(f"Error fetching round history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fl/rounds/{round_number}/metrics", tags=["FL Operations"])
async def log_round_results(
    round_number: int,
    num_clients: int = 0,
    aggregated_loss: float = 0.0,
    aggregated_accuracy: float = 0.0
) -> dict:
    """
    Log metrics for a completed round
    Called by Flower server or monitoring service
    """
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            round_data = await fl_repository.get_round_by_number(session, round_number)
            
            if not round_data:
                raise HTTPException(status_code=404, detail=f"Round {round_number} not found")
            
            # Update round with metrics
            round_data.num_clients = num_clients
            round_data.aggregated_loss = aggregated_loss
            round_data.aggregated_accuracy = aggregated_accuracy
            round_data.status = "completed"
            
            await fl_repository.update_round(session, round_data)
            
            logger.info(
                f"✅ Round {round_number} metrics logged: "
                f"{num_clients} clients, loss={aggregated_loss:.4f}, acc={aggregated_accuracy:.4f}"
            )
            
            return {
                "status": "success",
                "round_number": round_number,
                "num_clients": num_clients,
                "aggregated_loss": aggregated_loss,
                "aggregated_accuracy": aggregated_accuracy
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging round metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics & Analytics Endpoints
# ============================================================================

@app.get("/fl/stats/participation", tags=["Analytics"])
async def get_participation_stats() -> dict:
    """Get client participation statistics across all rounds"""
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            rounds = await fl_repository.get_all_rounds(session)
            
            if not rounds:
                return {"total_rounds": 0, "avg_clients": 0, "data": []}
            
            completed_rounds = [r for r in rounds if r.num_clients and r.num_clients > 0]
            
            if not completed_rounds:
                return {"total_rounds": len(rounds), "avg_clients": 0, "data": []}
            
            client_counts = [r.num_clients for r in completed_rounds]
            avg_clients = sum(client_counts) / len(client_counts)
            
            return {
                "total_rounds": len(completed_rounds),
                "avg_clients": round(avg_clients, 2),
                "min_clients": min(client_counts),
                "max_clients": max(client_counts),
                "data": [
                    {
                        "round_number": r.round_number,
                        "num_clients": r.num_clients,
                        "timestamp": r.created_at.isoformat()
                    }
                    for r in sorted(completed_rounds, key=lambda x: x.round_number)
                ]
            }
            
    except Exception as e:
        logger.error(f"Error calculating participation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fl/stats/performance", tags=["Analytics"])
async def get_performance_stats() -> dict:
    """Get model performance statistics (loss & accuracy trends)"""
    
    if not fl_repository:
        raise HTTPException(status_code=503, detail="FL Repository not initialized")
    
    try:
        async with AsyncSessionLocal() as session:
            rounds = await fl_repository.get_all_rounds(session)
            
            completed_rounds = [r for r in rounds if r.aggregated_loss is not None]
            
            if not completed_rounds:
                return {"total_rounds": 0, "best_round": None, "data": []}
            
            # Find best round (lowest loss, highest accuracy)
            best_by_loss = min(completed_rounds, key=lambda x: x.aggregated_loss or float('inf'))
            best_by_accuracy = max(completed_rounds, key=lambda x: x.aggregated_accuracy or 0.0)
            
            return {
                "total_rounds": len(completed_rounds),
                "best_loss": {
                    "round": best_by_loss.round_number,
                    "loss": best_by_loss.aggregated_loss
                },
                "best_accuracy": {
                    "round": best_by_accuracy.round_number,
                    "accuracy": best_by_accuracy.aggregated_accuracy
                },
                "trend": [
                    {
                        "round_number": r.round_number,
                        "loss": r.aggregated_loss,
                        "accuracy": r.aggregated_accuracy,
                        "timestamp": r.created_at.isoformat()
                    }
                    for r in sorted(completed_rounds, key=lambda x: x.round_number)
                ]
            }
            
    except Exception as e:
        logger.error(f"Error calculating performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": True,
        "status_code": exc.status_code,
        "detail": exc.detail,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
