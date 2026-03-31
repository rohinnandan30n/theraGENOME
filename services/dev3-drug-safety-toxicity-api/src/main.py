from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.drugs import router as drugs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Drug Safety & Toxicity API starting...")
    yield
    print("🛑 Shutting down")

app = FastAPI(
    title="TheraGenome — Drug Safety & Toxicity API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(drugs_router, prefix="/api/v1/drugs", tags=["Drugs"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "dev3-drug-safety-toxicity-api"}
